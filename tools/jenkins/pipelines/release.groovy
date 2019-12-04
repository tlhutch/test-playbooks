pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.6.x', '3.5.x', '3.4.x', '3.3.x']
        )
        choice(
            name: 'SCOPE',
            description: 'What is the scope of the verification? (Full will run all supported permutation, latest only on latest OSes)',
            choices: ['latest', 'full']
        )
    }

    options {
        timestamps()
        timeout(time: 20, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '10'))
    }

    stages {

        stage ('Build Information') {
            steps {
                echo """Tower version under test: ${params.TOWER_VERSION}
Scope selected: ${params.SCOPE}"""

                script {
                    if (params.TOWER_VERSION == '3.6.x' ) {
                        _TOWER_VERSION = '3.6.2'
                    } else if (params.TOWER_VERSION == '3.5.x') {
                        _TOWER_VERSION = '3.5.4'
                    } else if (params.TOWER_VERSION == '3.4.x') {
                        _TOWER_VERSION = '3.4.6'
                    } else if (params.TOWER_VERSION == '3.3.x') {
                        _TOWER_VERSION = '3.3.8'
                    } else {
                        _TOWER_VERSION = 'devel'
                    }

                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${_TOWER_VERSION}"
                    }
                }
            }
        }

        stage('Build Tower TAR') {
            steps {
                build(
                    job: 'Build_Tower_TAR',
                    parameters: [
                       string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                    ]
                )
            }
        }

        stage('Pipelines') {
            parallel {
                stage('Debian') {
                    when {
                        expression {
                            return _TOWER_VERSION ==~ /3.[3-5].[0-9]*/
                        }
                    }

                    steps {
                        build(
                            job: 'debian-pipeline',
                            parameters: [
                                string(name: 'TOWER_VERSION', value: _TOWER_VERSION),
                                string(name: 'SCOPE', value: params.SCOPE),
                            ]
                        )
                    }
                }
                stage('Red Hat') {
                    steps {
                        build(
                            job: 'redhat-pipeline',
                            parameters: [
                                string(name: 'TOWER_VERSION', value: _TOWER_VERSION),
                                string(name: 'SCOPE', value: params.SCOPE),
                            ]
                        )
                    }
                }
                stage('OpenShift') {
                    steps {
                        build(
                            job: 'openshift',
                            parameters: [
                                string(name: 'TOWER_VERSION', value: _TOWER_VERSION),
                                string(name: 'TRIGGER_BREW_PIPELINE', value: 'yes'),
                            ]
                        )
                    }
                }
                stage('Artifacts') {
                    steps {
                        build(
                            job: 'build-artifacts-pipeline',
                            parameters: [
                                string(name: 'TOWER_VERSION', value: _TOWER_VERSION),
                            ]
                        )
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                node('jenkins-jnlp-agent') {
                    withCredentials([string(credentialsId: 'jenkins_username', variable: 'JENKINS_USERNAME'),
                                     string(credentialsId: 'jenkins_token', variable: 'JENKINS_TOKEN')]) {
                        withEnv(["JENKINS_URL=http://jenkins.ansible.eng.rdu2.redhat.com",
                                 "JENKINS_USERNAME=${JENKINS_USERNAME}",
                                 "JENKINS_TOKEN=${JENKINS_TOKEN}"]) {
                            checkout([
                                $class: 'GitSCM',
                                branches: [[name: "*/${branch_name}" ]],
                                userRemoteConfigs: [
                                    [
                                        credentialsId: 'github-ansible-jenkins-nopassphrase',
                                        url: 'git@github.com:ansible/tower-qa.git'
                                    ]
                                ]
                            ])
                            sh 'pip install -Ur scripts/requirements.bots'
                            if (currentBuild.result == 'SUCCESS') {
                                color = 'good'
                            } else {
                                color = 'danger'
                            }
                            content = sh(
                                script: "RELEASE_PIPELINE_BUILD_ID=${env.BUILD_ID} python tools/bots/release_pipeline_results.py",
                                returnStdout: true
                            )
                            msg = "(#${env.BUILD_ID}) *Release Pipeline for Tower version:  ${_TOWER_VERSION}* | <${env.RUN_DISPLAY_URL}|Link>\n\n${content}"
                            slackSend(
                                botUser: false,
                                color: color,
                                teamDomain: "ansible",
                                channel: "#ship_it",
                                message: msg
                            )
                            slackSend(
                                botUser: false,
                                color: color,
                                teamDomain: "ansible",
                                channel: "#fortheloveofthegreen",
                                message: msg
                            )
                        }
                    }
                }
            }
        }
    }
}

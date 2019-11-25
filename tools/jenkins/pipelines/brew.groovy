pipeline {

    agent { label 'buildvm' }

    parameters {
        string(
            name: 'TOWER_FORK',
            description: 'Fork of tower to deploy',
            defaultValue: 'ansible'
        )
        string(
            name: 'TOWER_BRANCH',
            description: 'Branch to use for Tower',
            defaultValue: 'devel'
        )
        string(
            name: 'TOWER_PACKAGING_FORK',
            description: 'Fork of tower-packaging to deploy',
            defaultValue: 'ansible'
        )
        string(
            name: 'TOWER_PACKAGING_BRANCH',
            description: 'Branch to use for tower-packaging',
            defaultValue: 'devel'
        )
        choice(
            name: 'TARGET_DIST',
            description: 'mock environment to use',
            choices: ['epel-7-x86_64', 'epel-8-x86_64']
        )
        choice(
            name: 'OFFICIAL',
            description: 'Is this part of an official release ?',
            choices: ['no', 'yes']
        )
        choice(
            name: 'BUILD_CONTAINER',
            description: 'Should the container image be built ?',
            choices: ['yes', 'no']
        )
        choice(
            name: 'PUSH_CONTAINER',
            description: 'Should the container image be pushed ?',
            choices: ['yes', 'no']
        )
    }

    options {
        timestamps()
        timeout(time: 10, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage('Checkout tower-packaging') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${params.TOWER_PACKAGING_BRANCH}" ]],
                    userRemoteConfigs: [
                        [
                            credentialsId: 'github-ansible-jenkins-nopassphrase',
                            url: "git@github.com:${params.TOWER_PACKAGING_FORK}/tower-packaging.git"
                        ]
                    ]
                ])
            }
        }

        stage('Build Tower Brew RPM') {
            steps {
                withCredentials([string(credentialsId: 'red_hat_password', variable: 'RED_HAT_PASSWORD')]) {
                    withEnv(["OFFICIAL=${params.OFFICIAL}",
                             "TOWER_REPO=git@github.com:${params.TOWER_FORK}/tower.git",
                             "TOWER_BRANCH=${params.TOWER_BRANCH}",
                             "TARGET_DIST=${params.TARGET_DIST}",
                             "KEYTAB_FILE=/home/jenkins/ansible-tower-build.keytab",
                             "RED_HAT_USER=shanemcd@redhat.com",
                             "RED_HAT_PASSWORD=${RED_HAT_PASSWORD}"]) {
                        sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                            sh './tools/jenkins/scripts/build_brew_rpm.sh'
                        }
                    }
                }
            }
        }

        stage('Build Tower Brew Container Images') {
            when {
                expression {
                    return params.BUILD_CONTAINER == 'yes'
                }
            }

            steps {
                withEnv(["KEYTAB_FILE=/home/jenkins/ansible-tower-build.keytab",
                         "TOWER_BRANCH=${params.TOWER_BRANCH}"]) {
                    sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                        sh './tools/jenkins/scripts/build_brew_container.sh'
                    }
                }
                script {
                    BREW_CONTAINER_IMAGE = readFile('ansible-tower/BREW_CONTAINER_IMAGE').trim()
                }
                archiveArtifacts artifacts: 'ansible-tower/BREW_CONTAINER_IMAGE'
            }
        }

        stage('Push Brew Container Images') {
            when {
                expression {
                    return params.PUSH_CONTAINER == 'yes'
                }
            }

            agent { label 'jenkins-jnlp-agent' }

            steps {
                withCredentials([string(credentialsId: 'jenkins_token_ocp3_ansible_eng', variable: 'OPENSHIFT_TOKEN')]) {
                    withEnv(["OPENSHIFT_TOKEN=${OPENSHIFT_TOKEN}",
                             "BREW_CONTAINER_IMAGE=${BREW_CONTAINER_IMAGE}"]) {
                        sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                            checkout([
                                $class: 'GitSCM',
                                branches: [[name: "*/${params.TOWER_PACKAGING_BRANCH}" ]],
                                userRemoteConfigs: [
                                    [
                                        credentialsId: 'github-ansible-jenkins-nopassphrase',
                                        url: "git@github.com:${params.TOWER_PACKAGING_FORK}/tower-packaging.git"
                                    ]
                                ]
                            ])
                            sh './tools/jenkins/scripts/push_brew_container.sh'
                        }
                    }
                }
                archiveArtifacts artifacts: 'VERSION'
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}

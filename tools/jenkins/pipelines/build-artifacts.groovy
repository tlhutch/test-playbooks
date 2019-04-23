pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.5.0',
                      '3.4.4', '3.4.3', '3.4.2', '3.4.1', '3.4.0',
                      '3.3.6', '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0']
        )
    }

    options {
        timestamps()
    }

    stages {
        stage('Build Artifacts') {
            parallel {
                stage('Documentation') {
                    steps {
                        script {
                            stage('Documentation') {
                                if (params.TOWER_VERSION == 'devel') {
                                    branch = 'master'
                                } else {
                                    branch = "release_${params.TOWER_VERSION}"
                                }

                                build(
                                    job: 'Build_Tower_Docs',
                                    parameters: [
                                        string(name: 'GIT_BRANCH', value: "origin/${branch}"),
                                        string(name: 'OFFICIAL', value: 'no'),
                                    ]
                                )
                            }
                        }
                    }
                }

                stage('Vagrant Box') {
                    steps {
                        script {
                            stage('Vagrant Box') {
                                if (params.TOWER_VERSION == 'devel') {
                                    branch = 'devel'
                                } else {
                                    branch = "release_${params.TOWER_VERSION}"
                                }

                                build(
                                    job: 'Build_Tower_Vagrant_Box',
                                    parameters: [
                                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch}"),
                                        string(name: 'OFFICIAL', value: 'no'),
                                    ]
                                )
                            }
                        }
                    }
                }

                stage('AMI Image') {
                    steps {
                        script {
                            stage('AMI Image') {
                                if (params.TOWER_VERSION == 'devel') {
                                    branch = 'devel'
                                } else {
                                    branch = "release_${params.TOWER_VERSION}"
                                }

                                build(
                                    job: 'Build_Tower_Image',
                                    parameters: [
                                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch}"),
                                        string(name: 'OFFICIAL', value: 'no'),
                                        string(name: 'AW_REPO_URL', value: "http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/${branch}"),
                                    ]
                                )
                            }
                        }
                    }
                }
            }
        }
    }

}

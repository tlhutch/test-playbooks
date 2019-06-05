pipeline {

    agent none

    parameters {
        string(
            name: 'RHEL_COMPOSE_ID',
            description: 'RHEL Compose Id to test',
        )
    }

    options {
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage ('Pipeline Information') {
            steps {
                echo "Compose ID: ${params.RHEL_COMPOSE_ID}"
            }
        }

        stage ('Run Layered Product Testing pipelines') {
            parallel {
                stage ('Tower 3.3.5') {
                    when {
                        expression {
                            return ! params.RHEL_COMPOSE_ID.contains('RHEL-8');
                        }
                    }

                    steps {
                        build(
                            job: 'lptesting-pipeline',
                            parameters: [
                                string(name: 'RHEL_COMPOSE_ID', value: params.RHEL_COMPOSE_ID),
                                string(name: 'TOWER_VERSION', value: '3.3.5'),
                            ]
                        )
                    }
                }
                stage ('Tower 3.4.3') {
                    when {
                        expression {
                            return ! params.RHEL_COMPOSE_ID.contains('RHEL-8');
                        }
                    }

                    steps {
                        build(
                            job: 'lptesting-pipeline',
                            parameters: [
                                string(name: 'RHEL_COMPOSE_ID', value: params.RHEL_COMPOSE_ID),
                                string(name: 'TOWER_VERSION', value: '3.4.3'),
                            ]
                        )
                    }
                }
                stage ('Tower 3.5.0') {
                    steps {
                        build(
                            job: 'lptesting-pipeline',
                            parameters: [
                                string(name: 'RHEL_COMPOSE_ID', value: params.RHEL_COMPOSE_ID),
                                string(name: 'TOWER_VERSION', value: '3.5.0'),
                            ]
                        )
                    }
                }
            }
        }

    }

    post {
        success {
            slackSend(
                botUser: false,
                color: "good",
                teamDomain: "ansible",
                channel: "#ship_it",
                message: "*[Layered Product Testing] * Compose ID: ${params.RHEL_COMPOSE_ID} | <${env.RUN_DISPLAY_URL}|Link>"
            )
        }
        unsuccessful {
            slackSend(
                botUser: false,
                color: "#922B21",
                teamDomain: "ansible",
                channel: "#ship_it",
                message: "*[Layered Product Testing] * Compose ID: ${params.RHEL_COMPOSE_ID} | <${env.RUN_DISPLAY_URL}|Link>"
            )
        }
    }
}

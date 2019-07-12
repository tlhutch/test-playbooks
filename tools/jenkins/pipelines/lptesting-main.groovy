pipeline {

    agent none

    parameters {
        string(
            name: 'RHEL_COMPOSE_ID',
            description: 'RHEL Compose Id to test',
        )
        string(
            name: 'RHEL_IMAGE_NAME',
            description: 'RHEL Image Name on OpenStack (if diffent than RHEL_COMPOSE_ID)',
            defaultValue: '${RHEL_COMPOSE_ID}'
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
                stage ('Tower 3.3.6') {
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
                                string(name: 'RHEL_IMAGE_NAME', value: RHEL_IMAGE_NAME),
                                string(name: 'TOWER_VERSION', value: '3.3.6'),
                            ]
                        )
                    }
                }
                stage ('Tower 3.4.4') {
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
                                string(name: 'RHEL_IMAGE_NAME', value: RHEL_IMAGE_NAME),
                                string(name: 'TOWER_VERSION', value: '3.4.4'),
                            ]
                        )
                    }
                }
                stage ('Tower 3.5.1') {
                    steps {
                        build(
                            job: 'lptesting-pipeline',
                            parameters: [
                                string(name: 'RHEL_COMPOSE_ID', value: params.RHEL_COMPOSE_ID),
                                string(name: 'RHEL_IMAGE_NAME', value: RHEL_IMAGE_NAME),
                                string(name: 'TOWER_VERSION', value: '3.5.1'),
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

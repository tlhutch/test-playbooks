// Taken from here: https://gitlab.sat.engineering.redhat.com/cvp/pipeline/blob/master/samples/umb-interactions/Jenkinsfile

def ciMessage = params.CI_MESSAGE

def finalStatus = ''
def status = ''
def composeID = ''
def composeIDImage = ''
def composeVersion = ''
def towerVersion = ''
def taskID = 0
def milestone = ''

pipeline {

    agent { label 'jenkins-jnlp-agent' }

    stages {

        stage("Parse LP testing UMB message") {
            steps {
                script {
                    echo "Raw message:\n${ciMessage}"

                    def ciData = readJSON text: ciMessage

                    for (product in ciData['artifact']['products']) {
                        if (product['name'].toLowerCase() == "rhel") {
                            openstackImage = product['image']
                            composeID = product?.id
                            composeIDImage = product?.image
                            composeVersion = product?.version
                            milestone = product?.milestone
                        }
                        if (product['name'].toLowerCase() == "ansible_tower") {
                            towerVersion = product?.version
                        }
                    }

                    taskID = ciData?.artifact?.id

                    echo "${composeID} | ${composeIDImage} | ${towerVersion}"
                }
            }
        }

        stage("Run lptesting pipeline") {
            steps {
                script {
                    slackSend(
                        botUser: false,
                        teamDomain: "ansible",
                        channel: "#umb-events",
                        message: """*[LP Event]*: The Layered Product Interop testing team has emitted a new event.

A new Compose ID *${composeID}* is ready for testing. This event is for *Ansible Tower ${towerVersion}*

The <http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Pipelines/job/lptesting-pipeline/ | Layered Product Testing Pipeline> will be triggered with the following parameters:

• `RHEL_COMPOSE_ID`: `${composeID}`
• `RHEL_IMAGE_NAME`: `${composeIDImage}`
• `TOWER_VERSION`: `${towerVersion}`
"""
                    )
                    finalStatus = build(
                        job: 'Pipelines/lptesting-pipeline',
                        propagate: false,
                        parameters: [
                            string(name: 'RHEL_COMPOSE_ID', value: composeID),
                            string(name: 'RHEL_IMAGE_NAME', value: composeIDImage),
                            string(name: 'TOWER_VERSION', value: towerVersion),
                        ]
                    )

                    copyArtifacts filter: 'reports/junit/results-final.xml', fingerprintArtifacts: true, flatten: true, projectName: 'Pipelines/lptesting-pipeline', selector: specific("${finalStatus.number}")
                    sh 'yum install -y fpaste'
                    fpaste_url = sh(script: 'fpaste results-final.xml 2>/dev/null', returnStdout: true)
                    fpaste_url = fpaste_url.split(' ')[-1].trim()
                    fpaste_url = sh (
                        script: "echo ${fpaste_url} | sed 's#\\(.*\\)/\\(.*\\)#\\1/raw/\\2#g'",
                        returnStdout: true
                    ).trim()
                    echo "fpaste URL: ${fpaste_url}"

                    if (finalStatus.result == 'SUCCESS') {
                        status = 'passed'
                        color = 'good'
                        msg = """*[LP Event]*: For Compose ID - ${composeID} and Ansible Tower Version - ${towerVersion}

Following job has *succesfully* run: ${finalStatus.absoluteUrl}
Parameters used for the jobs are: ${finalStatus.absoluteUrl}/parameters/
Sending message to UMB to topic `VirtualTopic.qe.ci.product-scenario.test.complete` with `artifact.test.result` is `passed`
"""
                    } else {
                        currentBuild.result = finalStatus.result
                        status = 'failed'
                        color = 'danger'
                        msg = """*[LP Event]*: For Compose ID - ${composeID} and Ansible Tower Version - ${towerVersion}

Following job has *failed* to run: ${finalStatus.absoluteUrl}
Parameters used for the jobs are: ${finalStatus.absoluteUrl}/parameters/
Sending message to UMB to topic `VirtualTopic.qe.ci.product-scenario.test.complete` with `artifact.test.result` is `failed`
"""
                    }
                    slackSend(
                        botUser: false,
                        color: color,
                        teamDomain: "ansible",
                        channel: "#umb-events",
                        message: msg
                    )
                }
            }

            post {
                always {
                    script {
                        def msgContent = """
                          {
                            "contact": {
                                "name": "Ansible Tower QE",
                                "team": "Ansible Tower QE",
                                "docs": "https://docs.ansible.com/ansible-tower/latest/html/installandreference/index.html",
                                "email": "ansible-tower-qe@redhat.com",
                                "url": "https://www.ansible.com/products/tower"
                            },
                            "run": {
                                "url": "${finalStatus.absoluteUrl}",
                                "log": "${finalStatus.absoluteUrl}/console"
                            },
                            "artifact": {
                                "type": "product-scenario",
                                "id": "${taskID}",
                                "products": [
                                    {
                                        "name": "rhel",
                                        "version": "${composeVersion}",
                                        "distro": "${composeID}",
                                        "milestone": "${milestone}",
                                        "architecture": "x86_64",
                                    },
                                    {
                                        "name": "ansible-tower",
                                        "version": "${towerVersion}",
                                    }
                                ]
                            },
                            "test": {
                                "category": "interoperability",
                                "namespace": "interop",
                                "type": "product-scenario",
                                "result": "${status}",
                                "xunit_urls": ["${fpaste_url}raw"]
                            }
                          }"""

                        echo "Message to be send: ${msgContent}"
                        sendCIMessage(
                            messageContent: msgContent,
                            messageProperties: '',
                            messageType: 'Custom',
                            overrides: [topic: "VirtualTopic.qe.ci.product-scenario.test.complete"],
                            providerName: 'Red Hat UMB'
                        )
                    }
                }
            }
        }
    }

}

// Taken from here: https://gitlab.sat.engineering.redhat.com/cvp/pipeline/blob/master/samples/umb-interactions/Jenkinsfile


def ciMessage = params.CI_MESSAGE
def finalStatus = ''
def ErrataId = 0
def Component = ''
def status = ''
def TOWER_NAMESPACE = ''
def TOWER_VERSION = ''
def _TOWER_VERSION = ''
def TOWER_CONTAINER_IMAGE = ''
def MESSAGING_CONTAINER_IMAGE = ''
def MEMCACHED_CONTAINER_IMAGE = ''

pipeline {

    agent { label 'brew' }

    stages {

        stage("Parse 'redhat-container-group.test.queued' message") {
            steps {
                withCredentials([file(credentialsId: 'netrc_errata', variable: 'NETRC')]) {
                    script {
                        echo "Raw message:\n${ciMessage}"

                        def ciData = readJSON text: ciMessage
                        def images = ciData?.artifact?.images

                        Component = ciData?.artifact?.component
                        ErrataId = ciData?.artifact?.errata_id

                        // Retrieve the Tower Version impacted via the synopsis on the Errata advisory
                        //
                        TOWER_VERSION = sh (
                            script: "curl -k --netrc-file ${NETRC} https://errata.devel.redhat.com/api/v1/erratum/${ErrataId} 2>/dev/null | python -c 'import json,sys; print(json.loads(sys.stdin.read())[\"content\"][\"content\"][\"topic\"])' | sed 's/.*\\(3\\.[0-9]\\).*/\\1/g'",
                            returnStdout: true
                        ).trim()

                        if (TOWER_VERSION == '3.3') {
                            _TOWER_VERSION = '3.3.7'
                        } else if (TOWER_VERSION == '3.4') {
                            _TOWER_VERSION = '3.4.5'
                        } else {
                            _TOWER_VERSION = '3.5.3'
                        }

                        // Deduce the Toewr Namespace (ie. 35 for 3.5.x) for later consumption
                        TOWER_NAMESPACE = sh (
                            script: "echo ${_TOWER_VERSION} | sed 's/\\.//g' | sed s'/.\$//'",
                            returnStdout: true
                        ).trim()

                        images.each {
                            if (it.name == 'ansible-tower-messaging') {
                                MESSAGING_CONTAINER_IMAGE = it.full_name
                            }
                            if (it.name == 'ansible-tower-memcached') {
                                MEMCACHED_CONTAINER_IMAGE = it.full_name
                            }
                            if (it.name == 'ansible-tower') {
                                TOWER_CONTAINER_IMAGE = it.full_name
                            }
                        }
                    }
                }
            }
        }

        stage('Run openshift install tests') {
            steps {
                script {
                    slackSend(
                        botUser: false,
                        teamDomain: "ansible",
                        channel: "#umb-events",
                        message: """*[CVP Event]*: A new Errata has been automatically created for ${Component} *${_TOWER_VERSION}* (https://errata.engineering.redhat.com/advisory/${ErrataId}) following a CVE fixed in one of our dependencies.

List of emitted events for ${Component} are available on the <https://datagrepper.engineering.redhat.com/raw?topic=/topic/VirtualTopic.eng.ci.redhat-container-group.test.queued&delta=864000&contains=ansible-tower | UMB>

The <http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fopenshift-install-pipeline/activity | OpenShift Install> job will be triggered with the following parameters:

• `TOWER_VERSION` = ${_TOWER_VERSION?: '*Something is wrong this should always be set - please check the UMB message using the above link*'}
• `TOWER_CONTAINER_IMAGE` = ${TOWER_CONTAINER_IMAGE?: '`empty` - this container is not impacted by the CVE'}
• `MESSAGING_CONTAINER_IMAGE` = ${MESSAGING_CONTAINER_IMAGE?: '`empty` - this container is not impacted by the CVE'}
• `MEMCACHED_CONTAINER_IMAGE` = ${MEMCACHED_CONTAINER_IMAGE?: '`empty` - this container is not impacted by the CVE'}

"""
                    )
                    finalStatus = build(
                      job: 'Pipelines/openshift-integration-pipeline',
                      propagate: false,
                      parameters: [
                          string(name: 'TESTEXPR', value: 'yolo or ansible_integration'),
                          string(name: 'TOWER_VERSION', value: _TOWER_VERSION),
                          string(name: 'TOWER_CONTAINER_IMAGE', value: TOWER_CONTAINER_IMAGE),
                          string(name: 'MESSAGING_CONTAINER_IMAGE', value: MESSAGING_CONTAINER_IMAGE),
                          string(name: 'MEMCACHED_CONTAINER_IMAGE', value: MEMCACHED_CONTAINER_IMAGE),
                      ]
                    )
                    if (finalStatus.result == 'SUCCESS') {
                        color = "good"
                        msg = """*[CVP Event]*: For advisory https://errata.engineering.redhat.com/advisory/${ErrataId}

Following job has *succesfully* run: ${finalStatus.absoluteUrl}
Parameters used for the jobs are: ${finalStatus.absoluteUrl}/parameters/

Submitting results back to ResultsDB `ansible-tower-${TOWER_NAMESPACE}.default.integration` is `PASSED`
"""
                    } else {
                        currentBuild.result = finalStatus.result
                        color = "danger"
                        msg = """*[CVP Event]*: For advisory https://errata.engineering.redhat.com/advisory/${ErrataId}

Following job has *failed* to run: ${finalStatus.absoluteUrl}
Parameters used for the jobs are: ${finalStatus.absoluteUrl}/parameters/

Submitting results back to ResultsDB `ansible-tower-${TOWER_NAMESPACE}.default.integration` is `FAILED`
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
                        def provider = "Red Hat UMB"
                        def namespace = "ansible-tower-${TOWER_NAMESPACE}"
                        def type = "default"
                        def testName = "integration"
                        if (finalStatus.result == 'SUCCESS') {
                            status = 'PASSED'
                        } else {
                            status = 'FAILED'
                        }

                        def ciData = readJSON text: ciMessage
                        def images = ciData?.artifact?.images

                        images.each {
                            def brewTaskID = it.id
                            def brewNvr = it.nvr
                            def product = it.component

                            def msgContent = """
                             {
                                "category": "${testName}",
                                "status": "${status}",
                                "ci": {
                                    "url": "https://jenkins-cvp-ci.cloud.paas.upshift.redhat.com/",
                                    "team": "Ansible Tower QE",
                                    "email": "ansible-tower-qe@redhat.com",
                                    "name": "Ansible Tower QE"
                                },
                                "run": {
                                    "url": "${finalStatus.absoluteUrl}",
                                    "log": "${finalStatus.absoluteUrl}/console"
                                },
                                "system": {
                                    "provider": "openshift",
                                    "os": "openshift"
                                },
                                "artifact": {
                                    "nvr": "${brewNvr}",
                                    "component": "${product}",
                                    "type": "brew-build",
                                    "id": "${brewTaskID}",
                                    "issuer": "Unknown issuer"
                                },
                                "type": "${type}",
                                "version": "0.1.0",
                                "namespace": "${namespace}"
                              }"""

                            echo "Message to be send: ${msgContent}"
                            sendCIMessage(
                                messageContent: msgContent,
                                messageProperties: '',
                                messageType: 'Custom',
                                overrides: [topic: "VirtualTopic.eng.ci.brew-build.test.complete"],
                                providerName: provider
                            )

                        }

                    }
                }
            }
        }
    }

}

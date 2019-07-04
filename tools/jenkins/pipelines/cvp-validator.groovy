// Taken from here: https://gitlab.sat.engineering.redhat.com/cvp/pipeline/blob/master/samples/umb-interactions/Jenkinsfile

def ciMessage = params.CI_MESSAGE
def buildMetadata = [:]

library identifier: "contra-int-lib@master",
        retriever: modernSCM([$class: 'GitSCMSource',
                              remote: "https://gitlab.sat.engineering.redhat.com/contra/contra-int-lib.git"])

pipeline {
  agent none

  stages {
    stage("Parse 'redhat-container-image.pipeline.running' message") {
      steps {
        script {
          echo "Raw message:\n${ciMessage}"

          buildMetadata = extractCVPPipelineRunningMessageData(ciMessage)

          def metadataStr = buildMetadata
              .collect { meta -> "\t${meta.key} -> ${meta.value}"}
              .join("\n")
          echo "Build metadata:\n${metadataStr}"
        }
      }
    }

    stage("Run image tests") {
      steps {
          slackSend(
              botUser: false,
              color: "good",
              teamDomain: "ansible",
              channel: "#cvp-events",
              message: "${metadataStr}"
          )
      }
      post {
        always {
          script {
            def provider = "Red Hat UMB"
            def namespace = "ansible-tower"
            def type = "default"
            def testName = "functional"
            // Status can be 'PASSED', 'FAILED', 'INFO' (soft pass) or 'NEEDS_INSPECTION' (soft fail).
            // See Factory 2.0 CI UMB messages for more info - https://docs.google.com/document/d/16L5odC-B4L6iwb9dp8Ry0Xk5Sc49h9KvTHrG86fdfQM/edit#heading=h.ixgzbhywliel
            // TODO(spredzy): Retrieve status from integration_result.RESULT
            def status = "PASSED"

            def brewTaskID = buildMetadata['id']
            def brewNvr = buildMetadata['nvr']
            def product = buildMetadata['component']

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
                    "url": "${BUILD_URL}",
                    "log": "${BUILD_URL}/console"
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
                "namespace": "${namespace}"
              }"""

            echo "Sending the following message to UMB:\n${msgContent}"

            // sendCIMessage(
            //     messageContent: msgContent,
            //     messageProperties: '',
            //     messageType: 'Custom',
            //     overrides: [topic: "VirtualTopic.eng.ci.brew-build.test.complete"],
            //     providerName: provider
            // )
          }
        }
      }
    }
  }
}

pipelineJob('cvp-ansible-tower-container-testing-functional-trigger') {
  definition {

    parameters {
      stringParam("CI_MESSAGE", "", "Contents of the CI message received from UMB.")
    }

    triggers {
      ciBuildTrigger {
        providerData {
          activeMQSubscriberProviderData {
            name("Red Hat UMB")
            overrides {
              topic("Consumer.rh-jenkins-ci-plugin.85dd57c6-9e86-11e9-8de4-c85b7686606c.VirtualTopic.eng.ci.redhat-container-image.pipeline.running")
            }
            checks {
              msgCheck {
                field('$.artifact.type')
                expectedValue("cvp")
              }
              // msgCheck {
              //   field('$.artifact.nvr')
              //   expectedValue("^ansible-tower.*")
              // }
            }
          }
        }
        noSquash(true)
      }
    }

    cpsScm {
      scm {
        git {
          remote {
            url('git@github.com:ansible/tower-qa.git')
            credentials('d2d4d16b-dc9a-461b-bceb-601f9515c98a')
          }
          branch('*/devel')
        }
      }
      scriptPath('tools/jenkins/pipelines/cvp-validator.groovy')
      lightweight(false)
    }
  }
}

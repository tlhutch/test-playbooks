// Example of an event:
// https://datagrepper.engineering.redhat.com/id?id=ID:jenkins0-9-dxgbt-40434-1562733886163-633:1:1:1:1&is_raw=true&size=extra-large
//

pipelineJob('CVP Listener') {

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
                          topic("Consumer.rh-jenkins-ci-plugin.85dd57c6-9e86-11e9-8de4-c85b7686606c.VirtualTopic.eng.ci.redhat-container-group.test.queued")
                      }

                      checks {
                          msgCheck {
                              field('$.artifact.component')
                              expectedValue("Ansible Tower")
                          }
                          msgCheck {
                              field('$.artifact.type')
                              expectedValue("redhat-container-group")
                          }
                          msgCheck {
                              field('$.artifact.images[0].issuer')
                              expectedValue("freshmaker")
                          }
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
                      credentials('github-ansible-jenkins-nopassphrase')
                  }
                  branch('*/devel')
              }
          }

          scriptPath('tools/jenkins/pipelines/cvp-validator.groovy')
          lightweight(false)
      }

  }

}

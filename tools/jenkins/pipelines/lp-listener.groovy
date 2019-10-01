pipelineJob('Layered Product Testing Listener') {

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
                            topic("Consumer.rh-jenkins-ci-plugin.85dd57c6-9e86-11e9-8de4-c85b7612346c.VirtualTopic.qe.ci.product-scenario.build.complete")
                        }

                        checks {
                            msgCheck {
                                field('$..products.*.name')
                                expectedValue('ansible_tower')
                            }
                            msgCheck {
                                field('$..products.*.name')
                                expectedValue('rhel')
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
            scriptPath('tools/jenkins/pipelines/lp-validator.groovy')
            lightweight(false)
        }
    }

}

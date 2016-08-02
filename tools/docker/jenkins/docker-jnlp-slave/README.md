# Note!

This is a modified jnlp-slave image in order to serve as the parent image for jenkins-jnlp-docker-ansible.

The differences are:

- Remove the `VOLUME /home/jenkins` declaration so that we can store public keys in `/home/jenkins`. More info:
    - [https://github.com/docker/docker/issues/3465](https://github.com/docker/docker/issues/3465)
    - [https://docs.docker.com/engine/reference/builder/#volume](https://docs.docker.com/engine/reference/builder/#volume) ("Note: If any build steps change the data within the volume after it has been declared, those changes will be discarded.")

----

# Jenkins JNLP slave Docker image

[`jenkinsci/jnlp-slave`](https://hub.docker.com/r/jenkinsci/jnlp-slave/)

A [Jenkins](https://jenkins-ci.org) slave using JNLP to establish connection.

See [Jenkins Distributed builds](https://wiki.jenkins-ci.org/display/JENKINS/Distributed+builds) for more info.

Make sure your ECS container agent is [updated](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-update.html) before running. Older versions do not properly handle the entryPoint parameter. See the [entryPoint](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html#container_definitions) definition for more information.

## Running

To run a Docker container

    docker run jenkinsci/jnlp-slave -url http://jenkins-server:port <secret> <slave name>

optional environment variables:

* `JENKINS_URL`: url for the Jenkins server, can be used as a replacement to `-url` option, or to set alternate jenkins URL
* `JENKINS_TUNNEL`: (`HOST:PORT`) connect to this slave host and port instead of Jenkins server, assuming this one do route TCP traffic to Jenkins master. Useful when when Jenkins runs behind a load balancer, reverse proxy, etc.


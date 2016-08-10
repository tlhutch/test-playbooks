These are the Dockerfiles that are used to run on-demand Jenkins slaves inside of a Kubernetes cluster.

##### `docker-jnlp-slave`

This is a modified version of the official [`docker-jnlp-slave`](https://hub.docker.com/r/jenkinsci/jnlp-slave/). More info in that directory's README.

##### `jenkins-jnlp-docker-ansible`

This is an image that uses our modified `docker-jnlp-slave` as it's parent. It adds docker, docker-compose, and ansible to the slave container. More info in that directory's README.

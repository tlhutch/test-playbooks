This is an image that adds the following to the Jenkins containerized slave:

- docker
- docker-compose
- ansible / ansible-playbook, etc

The docker code was pulled from: [https://github.com/docker-library/docker/blob/7ef1746a46a29d89bac9aca8d0788bd629eb00e6/1.11/Dockerfile](https://github.com/docker-library/docker/blob/7ef1746a46a29d89bac9aca8d0788bd629eb00e6/1.11/Dockerfile)

In order for `docker` to work, `/var/run/docker.sock` must be mounted inside of the container.

This is a containerized Jenkins Agent that uses the [Swarm Plugin](https://wiki.jenkins-ci.org/display/JENKINS/Swarm+Plugin).
<small>_**Note:** This is not the same thing as [Docker Swarm](https://www.docker.com/products/docker-swarm)._</small>

### Building the image

There is nothing fancy about building this image, but it needs to be tagged correctly to work with [GCR](http://gcr.io):

```shell
$ cd tools/docker/jenkins/jenkins-swarm-agent
$ docker build -t gcr.io/ansible-tower-engineering/jenkins-swarm-agent .
```

### Pushing the image

```shell
$ gcloud docker push gcr.io/ansible-tower-engineering/jenkins-swarm-agent
```

### Running the image

This image is currently being deployed to [GKE](https://cloud.google.com/container-engine/), but will work on any Kubernetes cluster. The only prerequisites are the following environment variables:

- `JENKINS_USER`
- `JENKINS_TOKEN`

You can locate this information by logging into Jenkins and clicking your name at the top right, and navigating to your users "Configure" page. Click "Show API Token...".

These environment variables are injected into the container via a [Kubernetes Secret](http://kubernetes.io/docs/user-guide/secrets/#using-secrets-as-environment-variables). (See `replication.yml`)

To create the secret, run:

```shell
$ kubectl create secret generic jenkins-credentials \
    --from-literal=jenkins-user=user@ansible.com \
    --from-literal=jenkins-token=2db26x1a9a7ca97ad492748a818g2m7
```

Once the secret has been created, the agent(s) can be started by:

```shell
$ kubectl create -f replication.yml
```

To scale the number of agents:

```shell
$ kubectl scale --replicas=15 -f replication.yml
```

## Running py.test commands using the tower-qe container image
```shell
docker run -v $(pwd):/tower-qa gcr.io/ansible-tower-engineering/tower-qe py.test
```
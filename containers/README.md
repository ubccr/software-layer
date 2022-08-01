# CCR builder containers

CCR uses containers to build software modules. The build-node docker container
images are currently hosted on [docker hub](https://hub.docker.com/r/ubccr/build-node).

Currenty we support the following distros:

- debian10
- debian11
- ubuntu22.04
- ubuntu20.04
- flatcar (ccr custom image)

To build a new container image run:

## Re-building a build-node container image

1. Build container image:

```
$ docker build -t ubccr/build-node:ubuntu22.04 -f Dockerfile.CCR-build-node-ubuntu22.04 .
```

2. Push container up to docker hub:

```
# If you haven't previously authenticated, you need to do that first
$ docker login -u USERNAME

$ docker push ubccr/build-node:ubuntu22.04
```

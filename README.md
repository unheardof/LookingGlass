# LookingGlass
A collaborative network / infrastructure visualization tool oriented towards use for defensive and offensive cyber operations

# Project structure

References:

- https://github.com/docker/awesome-compose/tree/master/nginx-flask-mysql
- https://flask.palletsprojects.com/en/2.3.x/patterns/packages/

Project structure:
```
.
├── compose.yaml
├── backend
│   ├── Dockerfile
│   ├── requirements.txt
│   └── looking_glass
│       └── app.py
├── db
│   └── password.txt
├── proxy
│   ├── Dockerfile
│   └── conf
└── scripts
```

# How to run server in container

1. From the project root: `docker compose up -d`
1. Navigate to the appropriate URL

# How to stop the container

`docker compose down`

# How to run locally (debug mode)

From the command line, execute: `FLASK_APP=looking_glass/app.py flask run`

This will make the application accessible locally at `http://127.0.0.1:5000`

To make the application accessible to other computers, add `--host=0.0.0.0` to the end of the command: `FLASK_APP=application.py flask run --host=0.0.0.0`

**Note:** this is not recommended for production use and exposing a local webserver on your machine over the network has potential security considerations. Please do this with care.

# How to setup Amazon Linux instance for Docker Compose installation

1. Install Docker: sudo yum install docker
1. Add user to the docker group: sudo usermod -aG docker $USER
1. Install Docker Compose (https://docs.docker.com/compose/install/linux/#install-using-the-repository)
   1. DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
   1. mkdir -p $DOCKER_CONFIG/cli-plugins
   1. curl -SL https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
   1. chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
1. Start Docker service: sudo service docker start
1. Start a new terminal session for the current user to refresh the user group membership

# Bundle for distribution

1. Run the `scripts/bundle_app.sh` script. Will create a bundled app file named `looking_glass.app`

# Run from bundle

1. Use the steps above (or run the `scripts/install_docker.sh` script) to install docker and docker compose on the server
1. Make the bundle executable: `chmod +x looking_glass.app`
1. Run the bundle: `./looking_glass.app`

## Stop the app

1. `cd looking_glass`
1. `docker compose down`

## Restart the app

1. `cd looking_glass`
1. `docker compose up -d --no-build`

# Debugging

1. Enable debugging, add the following lines to the `backend` portion of the `compose.yaml` file: ```
    stdin_open: true
    tty: true
```
1. Set a breakpoint in the application code: `import pdb; pdb.set_trace()`
1. Rebuild the containers: `./scripts/clean_build_and_run.sh`
1. Attach to the backend container; will drop you into a pdb session when the breakpoint is hit: `scripts/pdb_attach.sh`

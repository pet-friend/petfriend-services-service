# Docker usefull commands

### Build docker container

`docker-compose build`

### Start the docker container

`docker-compose up --build -d`

### Destroy docker container and volumes

`docker-compose down -v`

### Run commands inside the container from host

`docker exec <conatiner_name> <command>`

Example: `docker exec basic-setup-fastapi-1 sh scripts/make_migrations.sh`


### Enter the docker container

`docker exec -t -i <container_name> /bin/bash`

Example: `docker exec -t -i basic-setup-fastapi-1 /bin/bash`
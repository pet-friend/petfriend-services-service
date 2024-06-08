#!/bin/bash

# Default values
drop_db=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case "$1" in
    -d|--drop-db)
      drop_db=true
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
  shift
done

# Remove database data if the flag is set
if [ "$drop_db" = true ]; then
  echo "Dropping database data..."
  rm -r app/dev_volumes/db/data/*
  rm -r app/dev_volumes/azurite/data/*
fi

# Stop and remove containers, networks, and volumes defined in the docker-compose.yml file
echo "Dropping docker container..."
docker compose down -v

# Build and run containers in the background
echo "Starting docker container..."
docker compose up --build -d
docker compose logs --follow

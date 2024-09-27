#!/bin/bash

docker-compose down
docker pull ghcr.io/The-Level-Density-Group/NLD_database_website:master
docker image prune -f
docker-compose up -d
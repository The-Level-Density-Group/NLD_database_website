#!/bin/bash

docker-compose down
docker pull ghcr.io/the-level-density-group/nld_database_website:master
docker image prune -f
docker-compose up -d

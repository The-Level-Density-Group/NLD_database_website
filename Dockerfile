# syntax=docker/dockerfile:1

FROM python:3.9-slim-bullseye
SHELL ["/bin/bash", "-c"]

RUN mkdir wd
WORKDIR wd
RUN apt-get update && apt-get install -y libexpat1
COPY . .

ARG TARGETPLATFORM

COPY requirements.txt .
RUN python3.9 -m pip install -r requirements.txt

CMD [ "gunicorn", "--workers=8", "--threads=4", "-b 0.0.0.0:80", "app:server"]
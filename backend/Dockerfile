# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.9-alpine AS builder

WORKDIR /code

COPY pyproject.toml .
COPY looking_glass/ /code/looking_glass/

# Needed to install numpy
RUN apk --no-cache add musl-dev linux-headers g++

RUN pip3 install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip \
   pip3 install -r looking_glass/requirements.txt

ENV FLASK_APP looking_glass/app.py
ENV FLASK_ENV development
ENV FLASK_RUN_PORT 8000
ENV FLASK_RUN_HOST 0.0.0.0

EXPOSE 8000

CMD ["flask", "run"]

FROM builder AS dev-envs

RUN apk add git

RUN addgroup -S docker
RUN adduser -S --shell /bin/bash --ingroup docker vscode

# install Docker tools (cli, buildx, compose)
COPY --from=gloursdocker/docker / /

CMD ["flask", "run"]


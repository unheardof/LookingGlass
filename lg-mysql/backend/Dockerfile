# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.9-alpine AS builder

WORKDIR /code
COPY requirements.txt /code

# Needed to install numpy
RUN apk --no-cache add musl-dev linux-headers g++

RUN pip3 install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt
# RUN pip3 install --upgrade pip3 && pip3 install -r /code/requirements.txt

COPY . .

ENV FLASK_APP app.py
ENV FLASK_ENV development
ENV FLASK_RUN_PORT 8000
ENV FLASK_RUN_HOST 0.0.0.0

EXPOSE 8000

CMD ["flask", "run"]

FROM builder AS dev-envs

RUN <<EOF
apk update
apk add git
EOF

RUN <<EOF
addgroup -S docker
adduser -S --shell /bin/bash --ingroup docker vscode
EOF

# install Docker tools (cli, buildx, compose)
COPY --from=gloursdocker/docker / /

CMD ["flask", "run"]
# CMD ["sleep", "10000000"]
# CMD "python3"
# CMD ["sleep", "1000000"]

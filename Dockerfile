# syntax=docker/dockerfile:1.4

# FROM tiangolo/uwsgi-nginx-flask:python3.11

# ARG NGINX_CONF_FILE

# RUN apt-get update &&\
#     apt-get -y install gcc &&\
#     apt-get -y install openssl &&\
#     apt-get -y install libssl-dev

# TODO: Create web server user and use that for the pip install and for running the web app
# COPY ./requirements.txt /var/www/requirements.txt
# RUN pip install --upgrade pip && pip install -r /var/www/requirements.txt
# COPY ./looking_glass /looking_glass

# ENV LISTEN_PORT 80
# ENV LISTEN_PORT 443
# EXPOSE 443
# EXPOSE 80

# ENV STATIC_URL /static
# ENV STATIC_URL /lib
# ENV STATIC_URL /templates
# ENV STATIC_PATH /var/www/looking_glass/static
# ENV STATIC_PATH /var/www/looking_glass/lib
# ENV STATIC_PATH /var/www/looking_glass/templates
# COPY ./requirements.txt /var/www/requirements.txt

# RUN echo "NGINX_CONF_FILE: $NGINX_CONF_FILE"
# COPY $NGINX_CONF_FILE /etc/nginx/conf.d/default.conf

# RUN pip install --upgrade pip && pip install -r /var/www/requirements.txt

FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

RUN apt-get update &&\
    apt-get -y install gcc &&\
    apt-get -y install openssl &&\
    apt-get -y install libssl-dev

WORKDIR /app

COPY requirements.txt /app

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --upgrade pip3 &&
    pip3 install -r requirements.txt

COPY ./app

ENTRYPOINT ["python3"]
CMD ["app.py"]

FROM builder as dev-envs

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

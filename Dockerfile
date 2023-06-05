FROM python:3.9

WORKDIR /code

RUN apt-get update &&\
    apt-get -y install gcc &&\
    apt-get -y install openssl &&\
    apt-get -y install libssl-dev

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./looking_glass /code/looking_glass

CMD ["gunicorn", "--conf", "looking_glass/gunicorn_conf.py", "--bind", "0.0.0.0:80", "looking_glass.application:app"]

# FROM tiangolo/uwsgi-nginx-flask:python3.11

# ARG NGINX_CONF_FILE

# RUN apt-get update &&\
#     apt-get -y install gcc &&\
#     apt-get -y install openssl &&\
#     apt-get -y install libssl-dev

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


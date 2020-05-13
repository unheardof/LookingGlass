# Based on https://www.digitalocean.com/community/tutorials/how-to-build-and-deploy-a-flask-looking_glasslication-using-docker-on-ubuntu-18-04
FROM tiangolo/uwsgi-nginx-flask:python3.6
RUN apt-get update && \
    apt-get -y install gcc && \
    apt-get -y install openssl && \
    apt-get -y install libssl-dev
RUN pip install --upgrade pip

ENV LISTEN_PORT 80
ENV LISTEN_PORT 443
EXPOSE 443
EXPOSE 80

ENV STATIC_URL /static
ENV STATIC_URL /lib
ENV STATIC_URL /templates
ENV STATIC_PATH /var/www/looking_glass/static
ENV STATIC_PATH /var/www/looking_glass/lib
ENV STATIC_PATH /var/www/looking_glass/templates
COPY ./requirements.txt /var/www/requirements.txt
COPY ./custom_nginx.conf /etc/nginx/conf.d/default.conf

RUN pip install -r /var/www/requirements.txt


FROM gliderlabs/alpine:latest
MAINTAINER Yosef <yosef.yudilevich@gmail.com> 
LABEL Description="for running bb python api"

ADD . /app
WORKDIR /app
RUN apk-install python3 \
	python3-dev \
	py3-pip &&\
	pip3 install -r requirements.txt
ENV FLASK_APP=api.py
EXPOSE 5000
CMD ["flask", "run"]

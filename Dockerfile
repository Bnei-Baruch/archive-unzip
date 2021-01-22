FROM    python:3.6-alpine3.8

LABEL   maintainer="edoshor@gmail.com"

RUN apk --no-cache add \
    build-base \
    fontconfig \
    libreoffice \
    libxml2-dev \
    libxslt-dev \
    linux-headers \
    msttcorefonts-installer \
    openjdk8-jre \
    openssl \
    postgresql-dev \
    tidyhtml-dev \
    pcre \
    pcre-dev \
    wget && \
    update-ms-fonts && \
    fc-cache -f

RUN \
    wget https://github.com/jgm/pandoc/releases/download/2.1.3/pandoc-2.1.3-linux.tar.gz && \
    tar xvzf pandoc-2.1.3-linux.tar.gz --strip-components 1 -C /usr/local/ && \
    rm -f pandoc-2.1.3-linux.tar.gz && \
    apk del wget

COPY --from=mwader/static-ffmpeg:4.0.3 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:4.0.3 /ffprobe /usr/local/bin/

WORKDIR /app
COPY . .
COPY ./misc/wait-for /wait-for
RUN pip install --no-cache-dir -r requirements.txt

#RUN addgroup -S deploy && adduser -H -S deploy -G deploy -u 1088 && \
#    chown -R deploy:deploy /app

VOLUME /assets

ENV     FLASK_ENV=production
ENV     UWSGI_WSGI_FILE=wsgi.py
ENV     UWSGI_CALLABLE=app
ENV     UWSGI_SOCKET=0.0.0.0:5000
ENV     UWSGI_VACUUM=true
ENV     UWSGI_MASTER=true
ENV     UWSGI_PROCESSES=2
ENV     UWSGI_THREADS=4
ENV     UWSGI_DIE_ON_TERM=true
ENV     UWSGI_HTTP_AUTO_CHUNKED=true
ENV     UWSGI_HTTP_KEEPALIVE=true
ENV     UWSGI_LAZY_APPS=false
ENV     UWSGI_WSGI_ENV_BEHAVIOR=holy

#ENV     SOFFICE_BIN=/usr/bin/soffice
ENV     BASE_DIR=/assets
ENV     FFMPEG_BIN=/usr/local/bin/ffmpeg
ENV     LINKER_URL=https://cdn.kabbalahmedia.info/

EXPOSE  5000

#USER deploy:deploy

CMD ["uwsgi", "--show-config"]

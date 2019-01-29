FROM    python:3.6-alpine3.8

RUN apk --no-cache add \
    build-base \
    linux-headers \
    libxml2-dev \
    libxslt-dev \
    openssl \
    wget \
    tidyhtml-dev \
    git \
    postgresql-dev \
    openjdk8-jre \
    libreoffice \
    msttcorefonts-installer \
    fontconfig && \
    update-ms-fonts && \
    fc-cache -f

RUN \
    wget https://github.com/jgm/pandoc/releases/download/2.1.3/pandoc-2.1.3-linux.tar.gz && \
    tar xvzf pandoc-2.1.3-linux.tar.gz --strip-components 1 -C /usr/local/

COPY --from=mwader/static-ffmpeg:4.0.3 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:4.0.3 /ffprobe /usr/local/bin/

RUN \
    git clone https://github.com/Bnei-Baruch/archive-unzip && \
    cd archive-unzip && \
    pip install --no-cache-dir -r requirements.txt && \
    mkdir logs

ENV     UWSGI_CHDIR=archive-unzip
ENV     UWSGI_WSGI_FILE=wsgi.py
ENV     UWSGI_CALLABLE=app
ENV     UWSGI_HTTP_SOCKET=0.0.0.0:5000
ENV     UWSGI_VACUUM=true
ENV     UWSGI_MASTER=true
ENV     UWSGI_PROCESSES=3
ENV     UWSGI_THREADS=2
ENV     UWSGI_DIE_ON_TERM=true

ENV     SOFFICE_BIN=/usr/bin/soffice
ENV     FFMPEG_BIN=/usr/local/bin/ffmpeg
ENV     LINKER_URL=https://cdn.kabbalahmedia.info/

EXPOSE  5000
CMD     ["uwsgi"]

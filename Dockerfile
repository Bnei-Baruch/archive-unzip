FROM    python:3.6-alpine3.8

RUN apk --no-cache add \
    build-base \
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
    pip install -r requirements.txt && \
    mkdir logs

ENV     SOFFICE_BIN=/usr/bin/soffice
ENV     FFMPEG_BIN=/usr/local/bin/ffmpeg
ENV     FLASK_APP=archive-unzip/autoapp.py
EXPOSE  5000
CMD     ["flask", "run", "--host=0.0.0.0"]

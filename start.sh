#!/usr/bin/env bash

set +e
set -x

cd /sites/archive-unzip/ && source bin/activate && uwsgi --ini app.ini

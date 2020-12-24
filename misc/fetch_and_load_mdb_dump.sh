#!/bin/bash
set -x
set -e

cd ~
wget https://kabbalahmedia.info/assets/mdb_dump.sql.gz
gunzip mdb_dump.sql.gz
psql -d postgres -f mdb_dump.sql
rm -f mdb_dump.sql
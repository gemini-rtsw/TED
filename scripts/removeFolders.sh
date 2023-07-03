#!/bin/sh

source ./.env
rm -r ${DATA_PATH}/es01

rm -r ${DATA_PATH}/ls01
rm -r ${DATA_PATH}/ls01/db
rm -r ${DATA_PATH}/ls01/db/sincedb

rm -r ${DATA_PATH}/ls02/
rm -r ${DATA_PATH}/ls02/db
rm -r ${DATA_PATH}/ls02/db/sincedb
rm -r ${DATA_PATH}/ls02/db/completed
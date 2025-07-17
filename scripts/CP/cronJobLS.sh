#!/bin/sh

echo "30 08 * * * docker restart ls03" >> mycron
crontab mycron
rm mycron

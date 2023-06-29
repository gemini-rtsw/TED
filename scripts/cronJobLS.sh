#!/bin/sh

echo "30 08 * * * docker restart ls01" >> mycron

crontab mycron
rm mycron
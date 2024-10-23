#!/bin/sh

echo "30 08 * * * docker restart ls01" >> mycron
echo "*/5 * * * * /bin/bash /home/software/TED/scripts/filterF2logs.sh" > mycron
crontab mycron
rm mycron

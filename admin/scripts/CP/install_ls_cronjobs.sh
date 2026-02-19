#!/bin/bash
ssh -n cpoteddev-lv2 "ls /gemsoft/var/log/{cpo,sbf,serialcon} > /dev/null; docker restart ls-core ls-guiders ls-opstools"
ssh -n cpoteddev-lv3 "ls /gemsoft/var/log/{cpo,ghost,serialcon} > /dev/null; docker restart ls-ghost ls-gmos"

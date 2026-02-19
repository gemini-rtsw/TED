#!/bin/bash
date
ssh -n cpoteddev-lv1 "docker stats --no-stream"
ssh -n cpoteddev-lv2 "docker stats --no-stream"
ssh -n cpoteddev-lv3 "docker stats --no-stream"

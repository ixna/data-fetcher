#!/bin/sh

uwsgi --daemonize service.log --http :9121 --module api --callable app --enable-threads --master --processes 5
#!/bin/sh

uwsgi --http :9121 --module api --callable app --enable-threads --master --processes 5
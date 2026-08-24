#!/usr/bin/env bash

if [ -n "$1" ]; then
    sudo journalctl -u adaio.service --no-pager --since now --follow
else
    sudo tail -F /var/log/syslog | grep -e adaio
fi

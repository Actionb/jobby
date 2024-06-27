#!/usr/bin/env bash
# Download current jobby main from github and install it in ~/jobby.

set +e

# TODO: download from explicit releases
curl -fsL https://github.com/Actionb/jobby/archive/refs/heads/main.tar.gz -o /tmp/jobby.tar.gz
mkdir ~/jobby && tar -xf /tmp/jobby.tar.gz -C ~/jobby
cd ~/jobby/jobby-main
python3 install.py --uid=$(id -u) --gid=$(id -g) --password=supersecret
rm /tmp/jobby.tar.gz

set -e
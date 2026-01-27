#!/bin/bash
# install_chrome.sh - Script cài đặt Google Chrome cho Railway/Heroku buildpack
set -e

CHROME_VERSION=121.0.6167.85-1

apt-get update && \
  apt-get install -y wget unzip gnupg2 && \
  wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
  echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
  apt-get update && \
  apt-get install -y google-chrome-stable=$CHROME_VERSION || apt-get install -y google-chrome-stable && \
  rm -rf /var/lib/apt/lists/*

echo "Google Chrome installed!"

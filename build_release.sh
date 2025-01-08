#!/bin/bash
if [ ! -f Python-3.6.9.tgz ]; then
  wget https://www.python.org/ftp/python/3.6.9/Python-3.6.9.tgz
fi
if [ ! -f Python-3.10.14.tgz ]; then
  wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
fi
if [ ! -f pypy3.10-v7.3.16-linux64.tar.bz2 ]; then
  wget https://downloads.python.org/pypy/pypy3.10-v7.3.16-linux64.tar.bz2
fi
if [ -z $1 ]; then
  echo "version is required for the release build"
  echo "Usage: $0 <version>"
else
  echo "Building version $1"
  docker build . -t littleorange666/judge_server:$1
fi
FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update

RUN apt-get install sudo -y
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y
RUN apt-get install make -y
RUN apt-get install libseccomp-dev -y
RUN apt-get install cmake -y

RUN apt-get -y install gcc
RUN apt-get -y install g++
RUN apt-get -y install bzip2
RUN apt-get -y install openjdk-8-jdk-headless
RUN apt-get -y install openjdk-17-jdk-headless

RUN useradd judge -u 1500 --system --no-create-home
RUN useradd compile -u 1600 --system --no-create-home
RUN useradd running -u 1700 --system --no-create-home

COPY . /app

RUN pip3 install -r requirements.txt

WORKDIR /app/Judger
RUN mkdir build
WORKDIR /app/Judger/build
RUN cmake ..
RUN make
RUN make install

WORKDIR /app

RUN cp /app/Judger/bindings/Python/_judger/__init__.py /app/_judger.py
RUN mkdir /python
RUN mv Python-3.6.9.tgz /python
RUN mv Python-3.10.14.tgz /python
RUN mv pypy3.10-v7.3.16-linux64.tar.bz2 /python

WORKDIR /python

RUN tar jxvf pypy3.10-v7.3.16-linux64.tar.bz2
RUN rm pypy3.10-v7.3.16-linux64.tar.bz2
RUN mv pypy3.10-v7.3.16-linux64 pypy3.10.14

RUN tar zxvf Python-3.6.9.tgz
RUN rm Python-3.6.9.tgz
WORKDIR /python/Python-3.6.9
RUN ./configure --prefix=/python/python3.6.9
RUN make
RUN make install
WORKDIR /python
RUN rm -rf Python-3.6.9

RUN tar zxvf Python-3.10.14.tgz
RUN rm Python-3.10.14.tgz
WORKDIR /python/Python-3.10.14
RUN ./configure --prefix=/python/python3.10.14
RUN make
RUN sudo make install
WORKDIR /python
RUN rm -rf Python-3.10.14

WORKDIR /app

CMD python3 main.py
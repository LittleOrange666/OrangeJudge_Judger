FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update

RUN apt-get -y install sudo python3 python3-pip make libseccomp-dev cmake bzip2 # for setup and server

RUN apt-get -y install gcc g++ openjdk-8-jdk-headless openjdk-17-jdk-headless rustc # for supported languages

RUN useradd judge -u 1500 --system --no-create-home \
    && useradd compile -u 1600 --system --no-create-home \
    && useradd running -u 1700 --system --no-create-home

COPY . /app

RUN pip3 install -r requirements.txt

RUN mkdir /app/Judger/build
WORKDIR /app/Judger/build
RUN cmake ..
RUN make && make install

WORKDIR /app

RUN cp /app/Judger/bindings/Python/_judger/__init__.py /app/_judger.py
RUN mkdir /python

RUN tar jxvf pypy3.10-v7.3.16-linux64.tar.bz2 -C /python \
    && tar zxvf Python-3.6.9.tgz -C /python \
    && tar zxvf Python-3.10.14.tgz -C /python

RUN mv /python/pypy3.10-v7.3.16-linux64 /python/pypy3.10.14

WORKDIR /python/Python-3.6.9
RUN ./configure --prefix=/python/python3.6.9 --without-ensurepip
RUN make && make install

WORKDIR /python/Python-3.10.14
RUN ./configure --prefix=/python/python3.10.14 --without-ensurepip
RUN make && make install

WORKDIR /app

CMD python3 main.py
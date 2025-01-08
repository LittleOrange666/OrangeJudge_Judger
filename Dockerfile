FROM ubuntu:22.04 AS builder

WORKDIR /app

RUN apt-get update

RUN apt-get -y install gcc make libseccomp-dev cmake bzip2 --fix-missing # for setup and server

COPY . /app

RUN mkdir /app/Judger/build
WORKDIR /app/Judger/build
RUN cmake ..
RUN make

WORKDIR /app
RUN mkdir /python
RUN mkdir /python_out

RUN tar jxvf pypy3.10-v7.3.16-linux64.tar.bz2 -C /python \
    && tar zxvf Python-3.6.9.tgz -C /python \
    && tar zxvf Python-3.10.14.tgz -C /python

WORKDIR /python/Python-3.6.9
RUN ./configure --prefix=/python_out/python3.6.9 --without-ensurepip
RUN make && make install

WORKDIR /python/Python-3.10.14
RUN ./configure --prefix=/python_out/python3.10.14 --without-ensurepip
RUN make && make install

FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update &&\
    apt-get -y install sudo python3 python3-pip libseccomp-dev --fix-missing &&\
    apt-get -y install gcc g++ openjdk-8-jdk-headless openjdk-17-jdk-headless rustc --fix-missing &&\
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd judge -u 1500 --system --no-create-home \
    && useradd compile -u 1600 --system --no-create-home \
    && useradd running -u 1700 --system --no-create-home

COPY main.py requirements.txt /app/
COPY modules /app/modules

RUN pip3 install -r requirements.txt

COPY --from=builder /app/Judger/bindings/Python/_judger/__init__.py /app/_judger.py
COPY --from=builder --chmod=755 --link /app/Judger/output/libjudger.so /usr/lib/judger/libjudger.so

RUN mkdir /python
COPY --from=builder /python/pypy3.10-v7.3.16-linux64 /python/pypy3.10.14
COPY --from=builder /python_out/python3.6.9 /python/python3.6.9
COPY --from=builder /python_out/python3.10.14 /python/python3.10.14

CMD python3 main.py
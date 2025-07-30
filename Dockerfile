FROM ubuntu:22.04 AS builder

WORKDIR /app

RUN apt-get update

RUN apt-get -y install gcc make libseccomp-dev cmake --fix-missing

COPY Judger /app/Judger

RUN mkdir /app/Judger/build
WORKDIR /app/Judger/build
RUN cmake ..
RUN make

FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update &&\
    apt-get -y install sudo python3 python3-pip libseccomp-dev --fix-missing &&\
    apt-get -y install gcc g++ --fix-missing &&\
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd judge -u 1500 --system --no-create-home \
    && useradd compile -u 1600 --system --no-create-home \
    && useradd running -u 1700 --system --no-create-home

COPY main.py requirements.txt /app/
COPY modules /app/modules

RUN pip3 install -r requirements.txt

COPY --from=builder --chmod=755 --link /app/Judger/output/libjudger.so /usr/lib/judger/libjudger.so

CMD python3 main.py
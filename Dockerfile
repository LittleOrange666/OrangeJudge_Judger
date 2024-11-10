FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update

RUN apt-get install sudo -y

RUN apt-get install python3 -y

RUN apt-get install python3-pip -y

RUN apt-get install make -y

RUN apt-get install libseccomp-dev -y

RUN apt-get install cmake -y

COPY . /app

WORKDIR /app/Judger

RUN mkdir build

WORKDIR /app/Judger/build

RUN cmake ..

RUN make

RUN make install

WORKDIR /app

RUN cp /app/Judger/bindings/Python/_judger/__init__.py /app/judger.py

CMD python3 -c "while True:pass"
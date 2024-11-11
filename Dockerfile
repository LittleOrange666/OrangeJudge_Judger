FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update

RUN apt-get install sudo -y

RUN apt-get install python3 -y

RUN apt-get install python3-pip -y

RUN apt-get install make -y

RUN apt-get install libseccomp-dev -y

RUN apt-get install cmake -y

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

RUN ./install_langs.sh

CMD python3 main.py
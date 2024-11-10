sudo apt-get -y install gcc
sudo apt-get -y install g++
sudo apt-get -y install bzip2
sudo apt-get -y install openjdk-8-jdk-headless
sudo apt-get -y install openjdk-17-jdk-headless
sudo apt-get -y install openjdk-17-jdk-headless
mkdir /python
sudo mv Python-3.6.9.tgz /python
sudo mv Python-3.10.14.tgz /python
sudo mv pypy3.6-v7.3.2-linux64.tar.bz2 /python
sudo mv pypy3.10-v7.3.16-linux64.tar.bz2 /python
sudo ./install_python.sh
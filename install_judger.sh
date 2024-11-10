cd Judger
sudo apt-get install libseccomp-dev -y
sudo apt-get install pipx -y
sudo apt-get install cmake -y
mkdir build
cd build
cmake ..
make
sudo make install
cd ../bindings/Python
sudo pipx install .

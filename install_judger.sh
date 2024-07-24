cd Judger
sudo apt-get install libseccomp-dev
sudo apt-get install pipx
mkdir build
cd build
cmake ..
make
sudo make install
cd ../bindings/Python
sudo pipx install .

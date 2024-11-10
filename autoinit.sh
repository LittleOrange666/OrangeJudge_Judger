sudo apt-get update
sudo apt-get -y install python3
sudo apt-get -y install python3-pip
sudo pip3 install -r requirements.txt
sudo useradd judge -u 1500 --system --no-create-home
sudo useradd compile -u 1600 --system --no-create-home
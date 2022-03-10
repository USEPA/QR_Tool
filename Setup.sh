#!/bin/bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install libffi-dev
sudo apt-get install libssl-dev
sudo apt-get install libatlas-base-dev -y
sudo apt-get install cmake -y
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade numpy
python3 -m pip install virtualenv
python3 -m virtualenv env
source env/bin/activate
curl https://sh.rustup.rs -sSf | sh -s -- -y
python -m pip install -r requirements.txt
sudo reboot
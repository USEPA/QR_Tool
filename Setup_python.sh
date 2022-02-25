#!/bin/bash
CURDIR=${PWD#*'pi/'}
cd || exit
wget https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz
tar -zxvf Python-3.9.5.tgz
cd Python-3.9.5 || exit
./configure --enable-optimizations
sudo make altinstall
cd || exit
cd /usr/bin || exit
sudo rm python
sudo ln -s /usr/local/bin/python3.9 python
python --version
cd || exit
sudo apt-get update
sudo apt-get upgrade
python -m pip install --upgrade pip
sudo python -m pip install virtualenv
cd "$CURDIR" || exit

#!/bin/bash
sudo apt-get update
alias python="python3"
alias pip="pip3"
pip install virtualenv
virtualenv env
source env/bin/activate
curl https://sh.rustup.rs -sSf | sh -s -- -y
sudo apt-get install libffi-dev
sudo apt-get install libssl-dev
pip install -r requirements.txt
source QR_Tool.sh
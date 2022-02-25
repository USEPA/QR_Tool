#!/bin/bash
source Setup_python.sh
virtualenv env
source env/bin/activate
curl https://sh.rustup.rs -sSf | sh -s -- -y
sudo apt-get install libffi-dev
sudo apt-get install libssl-dev
python -m pip install -r requirements.txt
source QR_Tool.sh
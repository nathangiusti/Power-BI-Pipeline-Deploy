#!/bin/sh
pip install --upgrade pip
pip install requests
pip install pyyaml
python /scripts/pipeline_deploy.py $1
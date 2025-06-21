#!/bin/bash

# Optional: activate your virtualenv (not needed if service does it)
# source /home/ec2-user/pollrot/venv/bin/activate

# Restart the Gunicorn service
sudo systemctl restart gunicorn
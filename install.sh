#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y python3 ffmpeg espeak-ng git fonts-dejavu-core
python3 momentmeter.py check

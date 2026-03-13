#!/bin/bash
# WallPi startup script
# Stops PipeWire and filters ALSA spam from output

cd ~/wall-e-robot
systemctl --user stop pipewire.socket pipewire-pulse.socket pipewire pipewire-pulse wireplumber 2>/dev/null

source venv/bin/activate
python main.py 2> >(grep -v "ALSA lib\|jack\|Jack\|Cannot connect\|JackShm" >&2)

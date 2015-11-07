#!/bin/bash

export DISPLAY=:0.0
files=(/home/asui/pictures/wallpaper/*)
wallpaper=(${files[RANDOM % ${#files[@]}]})
$(nitrogen --set-scaled --save "$wallpaper")

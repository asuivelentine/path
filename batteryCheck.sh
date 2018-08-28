#!/bin/bash

line=$(acpi -V | head -n1) 
v=$(echo "$line" | egrep -o '[0-9]?..(.)?%' | tr -d '%')

DISPLAY=0.0 $(xsetroot -name "bat: $v%")

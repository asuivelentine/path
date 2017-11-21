#!/bin/bash

v=$(acpi -V | head -n1 | grep -o '..%' | tr -d '%')

if [[ $v -lt 15 ]]; then
	i3-nagbar -m 'low battery'
fi


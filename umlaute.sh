#!/bin/bash

echo $1

sed -i s/+ae/ä/g $1
sed -i s/+oe/ö/g $1
sed -i s/+ue/ü/g $1

sed -i s/+AE/Ä/g $1
sed -i s/+OE/Ö/g $1
sed -i s/+UE/Ü/g $1

sed -i s/+ss/ß/g $1

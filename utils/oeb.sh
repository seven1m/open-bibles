#!/bin/bash

# Download the OEB version and format to OSIS since it is distributed as USFM.

rm -rf oeb
curl -o oeb.zip https://openenglishbible.org/oeb/2020.2/OEB-2020.2-US.usfm.zip
unzip -d oeb oeb.zip
python u2o.py -o ../eng-us-oeb.osis.xml oeb/usfm/*

rm -rf oeb
curl -o oeb.zip https://openenglishbible.org/oeb/2020.2/OEB-2020.2-Cth.usfm.zip
unzip -d oeb oeb.zip
python u2o.py -o ../eng-commonwealth-oeb.osis.xml oeb/usfm/*

rm oeb.zip
rm -rf oeb

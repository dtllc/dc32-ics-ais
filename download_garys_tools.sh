#!/bin/sh

set -ex

wget "https://www.garykessler.net/software/ais_tools_latest.zip"
unzip ais_tools_latest.zip
cp -R ais_tools_20240601_latest/* .
rm -rf ais_tools_20240601_latest
rm -rf __MACOSX

#!/bin/sh
dir=`dirname $0`
python3 -m pyedm -m PREFIX=BOC0000:102 \
	-m P=gw \
	-m baseDir=. \
	-m MYMACRO=MyMacro \
	"$@" \
	${dir}/testDir/*.jedl ${dir}/testDir/*.edl

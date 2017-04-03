#!/bin/bash

for surname in $(cut -d , -f 2 $1 | cut -d ' ' -f 2 | cut -d - -f 1 | cut -d / -f 1 | grep -v -e '^..$' | grep -v -e '^.$' | sort | uniq); do
	echo ${surname^}
done

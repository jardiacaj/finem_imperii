#!/bin/bash

for surname in $(cut -d , -f 1 $1 | cut -d - -f 1 | cut -d / -f 1 | sort | uniq -i); do
	echo ${surname^}
done

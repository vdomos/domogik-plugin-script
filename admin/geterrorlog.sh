#!/bin/bash

ERROR=$(grep ERROR /var/log/domogik/script.log |sort -rnk1,2 | head -10)
if [ -z $ERROR ]
then
	echo "Hooray, No error."
fi

#!/bin/bash
minutes=$(date "+%M")
echo $(($minutes % 2))  
exit 0

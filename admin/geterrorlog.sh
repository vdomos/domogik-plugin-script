#!/bin/bash

grep ERROR /var/log/domogik/xplplugin_script.log |sort -rnk1,2 | head -20
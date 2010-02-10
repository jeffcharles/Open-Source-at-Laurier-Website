#!/bin/sh

source local_variables.sh
python $PATH_TO_NOTIFICATION_MODULE/management/commands/emit_notices.py >> ../logs/cron_emit_notices.log 2>&1

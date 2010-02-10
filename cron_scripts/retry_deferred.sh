#!/bin/sh

source local_variables.sh
python $PATH_TO_MAILER_MODULE/management/commands/retry_deferred.py >> ../logs/cron_retry_deferred.log 2>&1

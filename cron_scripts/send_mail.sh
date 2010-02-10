#!/bin/sh

source local_variables.sh
python $PATH_TO_MAILER_MODULE/management/commands/send_mail.py >> ../logs/cron_send_mail.log 2>&1

#!/bin/bash

NAME="website.sms"                                  # Name of the application
DJANGODIR=/opt/website.smsgateway/deploy                 # Django project directory
SOCKFILE=/opt/website.smsgateway/tmp/gunicorn.sock                                                 # we will communicte using this unix socket
USER=root                                      # the user to run as
GROUP=root                                    # the group to run as
NUM_WORKERS=2                                   # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=config.settings            # which settings file should Django use
DJANGO_WSGI_MODULE=config.wsgi                     # WSGI module name
LOGFILE=/opt/website.smsgateway/logs/gunicorn.log
TIMEOUT=30

echo "Starting $NAME"

# Activate the virtual environment
cd $DJANGODIR
source /opt/website.smsgateway/.venv/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Create the log directory if it doesn't exist
LOGDIR=$(dirname $LOGFILE)
test -d $LOGDIR || mkdir -p $LOGDIR


# Migrate
python manage.py migrate
python manage.py collectstatic --noinput



# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
echo "start website django"



exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --timeout $TIMEOUT \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=$LOGFILE
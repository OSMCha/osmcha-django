#!/bin/sh
set -e

postgres_ready() {
python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect("") # use environment variables for connection
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing..."
exec $@

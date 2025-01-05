#!/bin/bash

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# Configuration for psql to be used throughout the script
psql=( psql --username "$PGUSER" )

# Create the 'template_postgis_pgvector' template db
"${psql[@]}" <<- 'EOSQL'
CREATE DATABASE template_postgis_pgvector ;
EOSQL

# Load PostGIS and PGVector into both template_database and $POSTGRES_DB
for DB in template_postgis_pgvector "$POSTGRES_DB"; do
	echo "Loading PostGIS and PGVector extensions into $DB"
	"${psql[@]}" --dbname="$DB" <<-'EOSQL'
		CREATE EXTENSION IF NOT EXISTS postgis;
		CREATE EXTENSION IF NOT EXISTS postgis_topology;
		-- Reconnect to update pg_setting.resetval
		-- See https://github.com/postgis/docker-postgis/issues/288
		\c
		CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
		CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
        
		CREATE EXTENSION IF NOT EXISTS vector;
EOSQL
done

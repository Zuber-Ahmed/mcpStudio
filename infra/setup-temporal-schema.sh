#!/bin/sh
set -eu
for database in temporal temporal_visibility; do
  temporal-sql-tool --ep postgres --port 5432 --user mcpstudio_local --pw "$POSTGRES_PWD" --pl postgres12 --db "$database" setup-schema --version 0.0
  schema=temporal
  if [ "$database" = temporal_visibility ]; then schema=visibility; fi
  temporal-sql-tool --ep postgres --port 5432 --user mcpstudio_local --pw "$POSTGRES_PWD" --pl postgres12 --db "$database" update-schema --schema-dir "/etc/temporal/schema/postgresql/v12/$schema/versioned"
done

#!/bin/bash
# refresh_staging.sh — wipe staging DB and restore from latest Kizuna production backup
set -e

BACKUP_DIR="/home/thierry/backups/konomocha"
LATEST=$(ls -t "$BACKUP_DIR"/kizuna_db_*.sql.gz 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
  echo "No backup found in $BACKUP_DIR"
  exit 1
fi

echo "Restoring staging from: $LATEST"

docker exec inventory-system-db-1 psql -U inventory -d inventorydb \
  -c "DROP DATABASE IF EXISTS konomocha_crm_staging;"
docker exec inventory-system-db-1 psql -U inventory -d inventorydb \
  -c "CREATE DATABASE konomocha_crm_staging OWNER konomocha_crm;"

gunzip -c "$LATEST" | PGPASSWORD='ZyF^#O9x' psql -h localhost -p 5432 -U konomocha_crm -d konomocha_crm_staging

echo "Staging database refreshed from $LATEST"

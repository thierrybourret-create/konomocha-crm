# Kizuna CRM — Backup Restore Procedure

**Last drill:** 2026-05-21 — PASSED  
Row counts after restore matched production: contacts 12,586 · pipeline_entries 266 · orders 0

---

## Backup locations

| Location | Path | Retention |
|----------|------|-----------|
| VPS local | `/home/thierry/backups/konomocha/kizuna_db_YYYY-MM-DD.sql.gz` | 30 days |
| OneDrive | `Kizuna-Backups/` | 30 days |

Backups run nightly at 02:15 via `/home/thierry/bin/kizuna_backup.sh`.

---

## Restore to staging (test drill)

Use this to verify a backup is valid, or to refresh staging with production data.

```bash
# Run the refresh script (drops and recreates staging DB from latest backup)
/home/thierry/konomocha-crm/scripts/refresh_staging.sh
```

Then verify row counts match production:

```bash
# Production counts
PGPASSWORD='ZyF^#O9x' psql -h localhost -p 5432 -U konomocha_crm -d konomocha_crm \
  -c "SELECT 'contacts', COUNT(*) FROM contacts
      UNION ALL SELECT 'pipeline_entries', COUNT(*) FROM pipeline_entries
      UNION ALL SELECT 'orders', COUNT(*) FROM orders;"

# Staging counts (should match)
PGPASSWORD='ZyF^#O9x' psql -h localhost -p 5432 -U konomocha_crm -d konomocha_crm_staging \
  -c "SELECT 'contacts', COUNT(*) FROM contacts
      UNION ALL SELECT 'pipeline_entries', COUNT(*) FROM pipeline_entries
      UNION ALL SELECT 'orders', COUNT(*) FROM orders;"
```

---

## Restore to production (disaster recovery)

Only use this if production data is lost or the database is corrupted.

```bash
# 1. Stop the production service
sudo systemctl stop konomocha-crm

# 2. Drop and recreate the production database
docker exec inventory-system-db-1 psql -U inventory -d inventorydb \
  -c "DROP DATABASE IF EXISTS konomocha_crm;"
docker exec inventory-system-db-1 psql -U inventory -d inventorydb \
  -c "CREATE DATABASE konomocha_crm OWNER konomocha_crm;"

# 3. Restore from the most recent backup
LATEST=$(ls -t /home/thierry/backups/konomocha/kizuna_db_*.sql.gz | head -1)
echo "Restoring from: $LATEST"
gunzip -c "$LATEST" | PGPASSWORD='ZyF^#O9x' psql -h localhost -p 5432 -U konomocha_crm -d konomocha_crm

# 4. Restart the service
sudo systemctl start konomocha-crm
sudo systemctl status konomocha-crm
```

---

## Restore from OneDrive (if VPS backups are unavailable)

```bash
# List available OneDrive backups
/home/thierry/bin/rclone ls onedrive:Kizuna-Backups/

# Download a specific backup
/home/thierry/bin/rclone copy "onedrive:Kizuna-Backups/kizuna_db_YYYY-MM-DD.sql.gz" \
  /home/thierry/backups/konomocha/

# Then follow the production restore steps above
```

---

## Drill log

| Date | Backup used | Result | Verified by |
|------|-------------|--------|-------------|
| 2026-05-21 | kizuna_db_2026-05-21.sql.gz | PASSED — row counts matched | Claude Code / Thierry |

# Quick Migration Reference

## I want to add/modify a column in the database

1. Edit `src/database.py` - modify the `Video` model
2. Generate migration:
   ```bash
   poetry run alembic revision --autogenerate -m "Add new_column to videos"
   ```
3. Review the file created in `alembic/versions/`
4. Apply it:
   ```bash
   poetry run alembic upgrade head
   ```

✅ Your data is preserved!

## Check what migrations are pending

```bash
poetry run alembic current
```

## View full migration history

```bash
poetry run alembic history
```

## Undo last migration

```bash
poetry run alembic downgrade -1
```

---

For more details, see [MIGRATIONS.md](MIGRATIONS.md)

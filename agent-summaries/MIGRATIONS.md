# Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations with SQLAlchemy.

## Common Commands

### Create a new migration after changing models

When you modify the database models in `src/database.py`, create a migration:

```bash
poetry run alembic revision --autogenerate -m "Description of changes"
```

This will:
- Compare your models with the current database schema
- Generate a migration file in `alembic/versions/`
- Include the changes needed to update the database

### Apply migrations

To apply all pending migrations to the database:

```bash
poetry run alembic upgrade head
```

### Rollback migrations

To rollback the last migration:

```bash
poetry run alembic downgrade -1
```

To rollback to a specific revision:

```bash
poetry run alembic downgrade <revision_id>
```

### Check current migration status

```bash
poetry run alembic current
```

### View migration history

```bash
poetry run alembic history --verbose
```

## Migration Workflow

1. **Modify your models** in `src/database.py`
2. **Generate migration**: `poetry run alembic revision --autogenerate -m "Add new column"`
3. **Review the migration** in `alembic/versions/` (always review auto-generated migrations!)
4. **Apply migration**: `poetry run alembic upgrade head`

## Example: Adding a New Column

Let's say you want to add a `category` column to the `Video` model:

1. Edit `src/database.py`:
   ```python
   class Video(Base):
       # ... existing columns ...
       category = Column(String(100), nullable=True, comment="Video category")
   ```

2. Generate migration:
   ```bash
   poetry run alembic revision --autogenerate -m "Add category column to videos table"
   ```

3. Review the generated file in `alembic/versions/`

4. Apply the migration:
   ```bash
   poetry run alembic upgrade head
   ```

The data in your table will be preserved!

## Important Notes

- **Always review** auto-generated migrations before applying them
- **Test migrations** on a development database first
- **Commit migration files** to version control
- **Never edit** applied migrations - create a new migration instead
- For complex changes, you may need to manually edit the generated migration

## Initial Setup (Already Done)

The project has been initialized with:
- `poetry run alembic init alembic` - Created migration environment
- Configured `alembic/env.py` to use our database connection
- Created initial migration capturing current schema
- Marked database as being at current version with `alembic stamp head`

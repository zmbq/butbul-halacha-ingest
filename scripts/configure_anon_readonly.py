"""
Configure Row Level Security (RLS) and policies to allow the Supabase `anon`
role read-only access to the public data tables.

This script will:
 - Enable RLS on these tables: videos, transcripts, video_metadata, alembic_version
 - Create/replace a SELECT policy for role `anon` on videos, transcripts, video_metadata
 - Do NOT grant anon access to the alembic_version table (RLS is enabled but no policy)

Usage:
  poetry run python scripts/configure_anon_readonly.py

Notes:
 - Requires that `DATABASE_URL` in the environment points to a PostgreSQL instance
   and the connecting role has privileges to ALTER TABLE and CREATE POLICY.
 - The script is idempotent: it drops existing policy named 'anon_select' and
   re-creates it.
"""
from urllib.parse import urlparse
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Ensure project root is on sys.path so `from src...` imports work when running
# this script directly (e.g. `python scripts/configure_anon_readonly.py`).
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from src.config import config


TABLES_WITH_ANNON_SELECT = ["videos", "transcripts", "video_metadata"]
ALL_TABLES = TABLES_WITH_ANNON_SELECT + ["alembic_version"]


def enable_rls_and_set_policy(conn, table: str, grant_anon: bool):
    with conn.cursor() as cur:
        # Enable RLS on the table
        cur.execute(sql.SQL("ALTER TABLE public.{} ENABLE ROW LEVEL SECURITY;").format(sql.Identifier(table)))

        if grant_anon:
            # Drop existing policy if exists, then create a simple policy allowing anon to SELECT
            cur.execute(sql.SQL("DROP POLICY IF EXISTS anon_select ON public.{};").format(sql.Identifier(table)))
            cur.execute(
                sql.SQL(
                    "CREATE POLICY anon_select ON public.{} FOR SELECT TO anon USING (true);"
                ).format(sql.Identifier(table))
            )


def main():
    db_url = config.database_url

    try:
        conn = psycopg2.connect(dsn=db_url)
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(2)

    try:
        for t in ALL_TABLES:
            grant = t in TABLES_WITH_ANNON_SELECT
            print(f"Configuring table: {t} (grant anon select: {grant})")
            try:
                enable_rls_and_set_policy(conn, t, grant)
            except Exception as e:
                print(f"  Error configuring {t}: {e}")

        conn.commit()
    finally:
        conn.close()

    print("Done. RLS enabled and policies created for anon on data tables.")


if __name__ == "__main__":
    main()

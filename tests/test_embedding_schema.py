import inspect
import pytest

from src import database


def test_embedding_has_no_text_field():
    Embedding = database.Embedding
    assert not hasattr(Embedding, 'text'), "Embedding model should not have 'text' column"


def test_source_cache_id_non_nullable():
    Embedding = database.Embedding
    col = getattr(Embedding, 'source_cache_id')
    # SQLAlchemy Column has .nullable attribute on its type info in __dict__
    nullable = getattr(col.property.columns[0], 'nullable', None)
    assert nullable is False, 'source_cache_id should be non-nullable'

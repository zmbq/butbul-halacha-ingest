import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from src.embedding_service import EmbeddingService
from src.database import EmbeddingCache


class FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *args, **kwargs):
        # For our fake, filtering is handled by caller; return self
        return self

    def all(self):
        return list(self._rows)

    def one(self):
        if len(self._rows) == 1:
            return self._rows[0]
        raise Exception('Expected one')


class FakeDB:
    def __init__(self):
        # store cache by (text, model)
        self._cache = {}
        self._added = []

    def query(self, model):
        # return FakeQuery over current cached rows
        rows = [v for v in self._cache.values()]
        return FakeQuery(rows)

    def add(self, row):
        # store row in added buffer; actual persistence on commit
        self._added.append(row)

    def commit(self):
        # persist added rows; raise IntegrityError if duplicate key
        for row in self._added:
            key = (row.text, row.model)
            if key in self._cache:
                self._added = []
                raise IntegrityError('duplicate', params=None, orig=Exception('dup'))
            self._cache[key] = row
        self._added = []

    def rollback(self):
        self._added = []


class DummyEmbeddingRow:
    def __init__(self, text, model, vector):
        self.text = text
        self.model = model
        self.vector = vector


def make_fake_openai_client(dim=3):
    class DummyEmbeddings:
        def create(self, model, input):
            # return a response-like object with .data list of dicts
            data = []
            for txt in input:
                # produce a deterministic vector based on text length for test
                vec = [float(len(txt) % 10 + i) for i in range(dim)]
                data.append({'embedding': vec})
            return {'data': data}

    class Client:
        def __init__(self):
            self.embeddings = DummyEmbeddings()

    return Client()


def test_embed_with_cache_hit():
    db = FakeDB()
    # pre-populate cache
    db._cache[('hello', 'text-embedding-3-small')] = DummyEmbeddingRow('hello', 'text-embedding-3-small', [1.0, 2.0, 3.0])

    svc = EmbeddingService(client=make_fake_openai_client())
    vecs = svc.embed_bulk(db, ['hello'])
    assert vecs == [[1.0, 2.0, 3.0]]


def test_embed_bulk_miss_and_store():
    db = FakeDB()
    svc = EmbeddingService(client=make_fake_openai_client(dim=4))
    texts = ['a', 'bb', 'ccc']
    vecs = svc.embed_bulk(db, texts)
    assert len(vecs) == 3
    # check that cache was populated
    for t, v in zip(texts, vecs):
        key = (t, svc.model)
        assert key in db._cache
        assert db._cache[key].vector == v


def test_race_condition_on_insert():
    db = FakeDB()
    svc = EmbeddingService(client=make_fake_openai_client(dim=2))

    # Simulate another process inserting during commit by pre-populating the cache
    db._cache[('x', svc.model)] = DummyEmbeddingRow('x', svc.model, [9.0, 9.0])

    # Request embedding for 'x' and 'y' where 'x' is already present
    vecs = svc.embed_bulk(db, ['x', 'y'])
    assert vecs[0] == [9.0, 9.0]
    # 'y' should have been created
    assert ('y', svc.model) in db._cache


def test_empty_input_returns_empty():
    db = FakeDB()
    svc = EmbeddingService(client=make_fake_openai_client())
    assert svc.embed_bulk(db, []) == []

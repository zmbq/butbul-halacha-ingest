"""Embedding service that consults DB cache and calls OpenAI embeddings API.

Features:
- Check `embeddings_cache` for existing embeddings (text+model) to avoid API calls.
- Use OpenAI batch embeddings when available to reduce API calls and cost.
- Store new embeddings in `embeddings_cache` with timestamps.

The service expects a SQLAlchemy session to be passed to methods (`db`), so the
caller controls transaction boundaries.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Tuple, Dict, Optional, cast, Any
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from src.database import EmbeddingCache
from src.database import get_db


@dataclass
class EmbeddingWithCache:
    vector: List[float]
    cache_row: Optional["EmbeddingCache"]


class EmbeddingService:
    """Service to get embeddings with DB caching.

    Usage:
        svc = EmbeddingService(model='text-embedding-3-small')
        with get_db() as db:  # or SessionLocal()
            vec = svc.embed(db, 'some text')

    The service will attempt to use the OpenAI Python client. It supports both
    the newer `OpenAI().embeddings.create(...)` client and the older
    `openai.Embedding.create(...)` interface.
    """

    def __init__(self, model: str = 'text-embedding-3-small', client: Any = None):
        self.model = model
        self.client: Any = client or self._make_client()

    def _make_client(self):
        # Use the newer OpenAI client (OpenAI class)
        try:
            from openai import OpenAI
            return OpenAI()
        except Exception as exc:
            raise RuntimeError('New OpenAI client not available; install openai>=1.0') from exc

    def _call_openai_batch(self, texts: List[str]) -> List[List[float]]:
        """Call OpenAI embeddings API for a batch of texts and return list of vectors.

        This method handles both the newer and older client shapes.
        """
        if not texts:
            return []

        # Use the new OpenAI client interface: client.embeddings.create
        embeddings_service = getattr(self.client, 'embeddings', None)
        if embeddings_service is None or not hasattr(embeddings_service, 'create'):
            raise RuntimeError('OpenAI client does not expose embeddings.create; ensure new client is installed')

        resp = embeddings_service.create(model=self.model, input=texts)
        data = getattr(resp, 'data', None)
        if data is None and isinstance(resp, dict):
            data = resp.get('data')
        if data is None:
            raise RuntimeError('Unexpected response shape from OpenAI client')

        embeddings: List[List[float]] = []
        for item in data:
            emb = item.get('embedding') if isinstance(item, dict) else getattr(item, 'embedding', None)
            if emb is None:
                raise RuntimeError('Missing embedding in OpenAI response item')
            embeddings.append(list(emb))
        return embeddings

    def embed(self, db, text: str) -> List[float]:
        """Return embedding vector for `text`, using cache when possible."""
        vectors = self.embed_bulk(db, [text])
        return vectors[0]

    def embed_bulk(self, db, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts, using cache and bulk OpenAI calls for missing items.

        Returns: list of vectors in the same order as `texts`.
        """
        if not texts:
            return []

        # Normalize texts to strings
        texts = [t if t is not None else '' for t in texts]

        # Query cache for existing embeddings
        existing = db.query(EmbeddingCache).filter(EmbeddingCache.text.in_(texts), EmbeddingCache.model == self.model).all()
        cache_map: Dict[str, EmbeddingCache] = {row.text: row for row in existing}

        # Prepare result list (Optional during construction)
        result_opt: List[Optional[List[float]]] = [None] * len(texts)

        # Fill from cache where available
        missing_texts: List[str] = []
        missing_indices: List[int] = []
        for idx, t in enumerate(texts):
            cached = cache_map.get(t)
            if cached is not None:
                # Try to coerce cached.vector to a python list
                try:
                    vec_list = list(cast(List[float], cached.vector))
                except Exception:
                    vec_list = [cast(float, cached.vector)]
                result_opt[idx] = cast(List[float], vec_list)
            else:
                missing_texts.append(t)
                missing_indices.append(idx)

        if not missing_texts:
            # cast to declared return type
            return [cast(List[float], v) for v in result_opt]

        # Call OpenAI in batch for missing texts
        embeddings = self._call_openai_batch(missing_texts)

        # Persist missing embeddings to cache and populate results
        now = datetime.now(timezone.utc)
        for i, vec in enumerate(embeddings):
            text_val = missing_texts[i]
            idx = missing_indices[i]
            result_opt[idx] = vec
            # Insert cache row; handle unique constraint race by catching IntegrityError
            try:
                row = EmbeddingCache(text=text_val, model=self.model, vector=vec, created_at=now, updated_at=now)
                db.add(row)
                db.commit()
            except IntegrityError:
                db.rollback()
                # Another process inserted the same cache entry; fetch it
                existing_row = db.query(EmbeddingCache).filter(EmbeddingCache.text == text_val, EmbeddingCache.model == self.model).one()
                # replace with canonical value if necessary
                try:
                    vec_list = list(cast(List[float], existing_row.vector))
                except Exception:
                    vec_list = [cast(float, existing_row.vector)]
                result_opt[idx] = cast(List[float], vec_list)

        # Finalize results: ensure no missing entries remain
        if any(v is None for v in result_opt):
            raise RuntimeError('Internal error: some embeddings are still missing after OpenAI call')

        final: List[List[float]] = [cast(List[float], v) for v in result_opt]
        return final

    def embed_bulk_with_cache(self, db, texts: List[str]) -> List[EmbeddingWithCache]:
        """Like embed_bulk, but return EmbeddingWithCache objects.

        This avoids callers having to re-query the cache table after embedding.
        Returns: list of EmbeddingWithCache in the same order as `texts`.
        """
        if not texts:
            return []

        # Normalize texts
        texts = [t if t is not None else '' for t in texts]

        # Query cache for existing embeddings
        existing = db.query(EmbeddingCache).filter(EmbeddingCache.text.in_(texts), EmbeddingCache.model == self.model).all()
        cache_map: Dict[str, EmbeddingCache] = {row.text: row for row in existing}

        # Prepare result containers
        result_opt: List[Optional[List[float]]] = [None] * len(texts)
        cache_rows: List[Optional[EmbeddingCache]] = [None] * len(texts)

        missing_texts: List[str] = []
        missing_indices: List[int] = []
        for idx, t in enumerate(texts):
            cached = cache_map.get(t)
            if cached is not None:
                try:
                    vec_list = list(cast(List[float], cached.vector))
                except Exception:
                    vec_list = [cast(float, cached.vector)]
                result_opt[idx] = cast(List[float], vec_list)
                cache_rows[idx] = cached
            else:
                missing_texts.append(t)
                missing_indices.append(idx)

        if missing_texts:
            embeddings = self._call_openai_batch(missing_texts)

            now = datetime.now(timezone.utc)
            for i, vec in enumerate(embeddings):
                text_val = missing_texts[i]
                idx = missing_indices[i]
                result_opt[idx] = vec
                # Insert cache row; handle unique constraint race
                try:
                    row = EmbeddingCache(text=text_val, model=self.model, vector=vec, created_at=now, updated_at=now)
                    db.add(row)
                    db.commit()
                    cache_rows[idx] = row
                except IntegrityError:
                    db.rollback()
                    existing_row = db.query(EmbeddingCache).filter(EmbeddingCache.text == text_val, EmbeddingCache.model == self.model).one()
                    cache_rows[idx] = existing_row
                    try:
                        vec_list = list(cast(List[float], existing_row.vector))
                    except Exception:
                        vec_list = [cast(float, existing_row.vector)]
                    result_opt[idx] = cast(List[float], vec_list)

        # Final checks
        if any(v is None for v in result_opt):
            raise RuntimeError('Internal error: some embeddings are still missing after OpenAI call')

        final: List[EmbeddingWithCache] = []
        for v, c in zip(result_opt, cache_rows):
            final.append(EmbeddingWithCache(vector=cast(List[float], v), cache_row=c))
        return final


__all__ = ['EmbeddingService']

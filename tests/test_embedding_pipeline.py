def test_embedding_pipeline_smoke_import():
    """Smoke test: importing the pipeline and calling dry-run on subjects (limit=5)."""
    from src.pipeline.s06_create_embeddings import populate_embeddings

    # Should not raise and should be safe to call in dry_run mode
    populate_embeddings('subjects', limit=5, batch_size=2, dry_run=True)

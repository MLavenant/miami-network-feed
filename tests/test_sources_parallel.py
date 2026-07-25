from collector.models import SourceResult
from collector.sources import SourceDef, collect_all


def test_parallel_collection_preserves_order_and_reuses_client_per_host(monkeypatch):
    import collector.sources as sources

    sample = [
        SourceDef("a", "A", "links", "https://one.example/events", ["hospitality"]),
        SourceDef("b", "B", "links", "https://one.example/calendar", ["hospitality"]),
        SourceDef("c", "C", "links", "https://two.example/events", ["hospitality"]),
    ]
    clients = {}

    def fake_fetch(client, src):
        clients[src.id] = client
        return SourceResult(src.id, src.name, True, 0, None, 1, [])

    monkeypatch.setattr(sources, "SOURCES", sample)
    monkeypatch.setattr(sources, "fetch_source", fake_fetch)
    results = collect_all()

    assert [result.source_id for result in results] == ["a", "b", "c"]
    assert clients["a"] is clients["b"]
    assert clients["a"] is not clients["c"]

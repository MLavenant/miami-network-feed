from collector.http_client import FetchResult
from collector.models import SourceResult
from collector.sources import SourceDef, collect_all, fetch_source


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


def test_backgammon_society_keeps_miami_and_localizes_wall_time():
    html = """
    <script type="application/ld+json">
    [
      {"@type":"Event","name":"Rare Collects","startDate":"2026-07-29T19:00:00",
       "url":"https://www.thebackgammonsociety.com/tournaments/miami/rare-collects",
       "location":{"@type":"Place","name":"Rare Collects",
       "address":{"@type":"PostalAddress","addressLocality":"Miami","streetAddress":"272 NW 36th St"}}},
      {"@type":"Event","name":"President Wilson Hotel","startDate":"2026-07-29T19:00:00",
       "url":"https://www.thebackgammonsociety.com/tournaments/geneva/hotel",
       "location":{"@type":"Place","name":"Hotel",
       "address":{"@type":"PostalAddress","addressLocality":"Geneva"}}}
    ]
    </script>
    """

    class FakeClient:
        def get(self, url):
            return FetchResult(True, url, 200, html, html.encode(), {})

    source = SourceDef(
        "backgammon_society",
        "The Backgammon Society",
        "jsonld",
        "https://www.thebackgammonsociety.com/",
        ["sports", "networking"],
        require_miami=True,
    )
    result = fetch_source(FakeClient(), source)

    assert result.ok
    assert len(result.events) == 1
    event = result.events[0]
    assert event.title == "Backgammon Society — Rare Collects"
    assert event.starts_at.isoformat() == "2026-07-29T19:00:00-04:00"
    assert event.access == "registration"


def test_backgammon_society_uses_reader_when_origin_blocks_ci():
    listing = """
    <script type="application/ld+json">
    [
      {"@type":"Event","name":"Rare Collects","startDate":"2026-07-29T19:00:00",
       "url":"https://www.thebackgammonsociety.com/tournaments/miami/rare-collects",
       "location":{"@type":"Place","name":"Rare Collects",
       "address":{"@type":"PostalAddress","addressLocality":"Miami","streetAddress":"272 NW 36th St"}}},
      {"@type":"Event","name":"Geneva Hotel","startDate":"2026-07-29T19:00:00",
       "url":"https://www.thebackgammonsociety.com/tournaments/geneva/hotel",
       "location":{"@type":"Place","name":"Hotel",
       "address":{"@type":"PostalAddress","addressLocality":"Geneva"}}}
    ]
    </script>
    """

    class FallbackClient:
        def get(self, url, **kwargs):
            if url == "https://www.thebackgammonsociety.com/":
                return FetchResult(False, url, 403, "", b"", {}, "HTTP 403")
            return FetchResult(True, url, 200, listing, listing.encode(), {})

    source = SourceDef(
        "backgammon_society",
        "The Backgammon Society",
        "jsonld",
        "https://www.thebackgammonsociety.com/",
        ["sports", "networking"],
        industry="sports",
        require_miami=True,
        access_tip="Use official registration.",
    )
    result = fetch_source(FallbackClient(), source)

    assert result.ok
    assert result.error is None
    assert len(result.events) == 1
    assert result.events[0].starts_at.isoformat() == "2026-07-29T19:00:00-04:00"
    assert result.events[0].industry == "sports"

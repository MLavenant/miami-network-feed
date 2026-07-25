from collector.http_client import FetchResult
from collector.models import RawEvent
from collector.people import extract_connectors


class FakeClient:
    def get(self, url: str) -> FetchResult:
        html = """
        <html><body>
          <h1>Delano Preview Dinner</h1>
          <div class="wp-caption-text">Seth Browarnik, Jane Connector, & One Time Guest</div>
          <div class="wp-caption-text">Seth Browarnik & Jane Connector</div>
        </body></html>
        """
        return FetchResult(True, url, 200, html, html.encode(), {})


def test_people_are_extracted_from_public_captions_with_sources():
    raw = RawEvent(
        title="Delano Preview Dinner",
        url="https://worldredeye.com/example/",
        source_id="world_red_eye",
    )
    people = extract_connectors(FakeClient(), [raw])
    seth = next(person for person in people if person["name"] == "Seth Browarnik")
    assert seth["role"] == "Founder"
    assert seth["organization"] == "World Red Eye"
    assert seth["source_urls"]
    assert "no face recognition" in seth["basis"].lower()

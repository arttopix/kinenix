"""#119: docs/llms.txt, served as https://www.kinenix.com/llms.txt, points AI assistants to pages that exist."""
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs"
REPO = DOCS.parent


def _links():
    return re.findall(r"\]\((https?://[^)\s]+)\)", (DOCS / "llms.txt").read_text(encoding="utf-8"))


def test_llms_txt_follows_the_format():
    text = (DOCS / "llms.txt").read_text(encoding="utf-8")
    assert text.startswith("# Kinenix\n\n> ")  # a title, then a one-paragraph summary
    assert re.findall(r"^## (.+)$", text, re.M)[-1] == "Optional"
    assert len(_links()) >= 10


def test_every_link_points_to_a_page_or_file_that_exists():
    for url in _links():
        site = re.fullmatch(r"https://www\.kinenix\.com/([\w/]+)/", url)
        github = re.fullmatch(r"https://github\.com/arttopix/kinenix/(?:blob|tree)/main/(.+)", url)
        assert site or github, f"{url}: link to www.kinenix.com pages or files of this repository"
        path = DOCS / f"{site.group(1)}.md" if site else REPO / github.group(1)
        assert path.exists(), f"{url}: {path} does not exist"

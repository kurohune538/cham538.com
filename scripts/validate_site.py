#!/usr/bin/env python3
"""Validate the built site's file references and sitemap without network access."""

from __future__ import annotations

import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


DIST = Path(__file__).resolve().parents[1] / "dist"


def local_target(source: Path, reference: str) -> Path | None:
    url = urlsplit(reference)
    if url.scheme or url.netloc or not url.path:
        return None
    path = unquote(url.path)
    return (DIST / path.lstrip("/") if path.startswith("/") else source.parent / path).resolve()


def exists(target: Path) -> bool:
    return target.is_relative_to(DIST.resolve()) and (
        target.is_file() or (target / "index.html").is_file()
    )


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src", "poster"):
            if values.get(key):
                self.urls.append(values[key])
        if values.get("srcset"):
            self.urls.extend(item.strip().split()[0] for item in values["srcset"].split(",") if item.strip())


def normalized_title(text: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).casefold())


def portfolio_link_errors(page: Path) -> list[str]:
    """Check card destinations, including valid pages for the wrong project."""
    errors = []
    seen = set()
    for anchor in re.finditer(r'<a\b([^>]*)>(.*?)</a>', page.read_text(encoding="utf-8"), re.DOTALL):
        title = re.search(r'class="text-block-(?:23|24)"[^>]*>(.*?)</div>', anchor[2], re.DOTALL)
        if not title:
            continue
        label = unescape(re.sub(r"<[^>]+>", "", title[1])).strip()
        href = re.search(r'href="([^"]*)"', anchor[1])
        reference = unescape(href[1]) if href else ""
        prefix = f"{page.relative_to(DIST)}: {label}"
        if not reference or reference == "#" or reference.startswith("javascript:"):
            errors.append(f"{prefix}: placeholder card link")
            continue
        destination = reference.rstrip("/")
        if destination in seen:
            errors.append(f"{prefix}: duplicate card destination {reference}")
        seen.add(destination)
        target = local_target(page, reference)
        if target is not None and exists(target):
            if target.is_dir():
                target /= "index.html"
            heading = re.search(r'<title\b[^>]*>(.*?)</title>', target.read_text(encoding="utf-8"), re.DOTALL)
            if heading:
                title_text = re.split(r"\s+[|–-]\s+", heading[1], maxsplit=1)[0]
                card_title, page_title = normalized_title(label), normalized_title(title_text)
                if page_title and page_title not in card_title and card_title not in page_title:
                    errors.append(f"{prefix}: destination title does not match ({reference})")
    return errors


def main() -> int:
    if not (DIST / "index.html").is_file():
        print("No built site. Run python3 scripts/build_mirror.py first.", file=sys.stderr)
        return 1
    errors: list[str] = []
    pages = sorted(DIST.rglob("*.html"))
    for page in pages:
        parser = References()
        text = page.read_text(encoding="utf-8")
        parser.feed(text)
        if "__SITE_" in text:
            errors.append(f"Unresolved template placeholder: {page.relative_to(DIST)}")
        for reference in parser.urls:
            target = local_target(page, reference)
            if target is not None and not exists(target):
                errors.append(f"{page.relative_to(DIST)}: missing {reference}")
    for css in DIST.rglob("*.css"):
        for reference in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", css.read_text(encoding="utf-8")):
            target = local_target(css, reference)
            if target is not None and not exists(target):
                errors.append(f"{css.relative_to(DIST)}: missing {reference}")

    for listing in ("works", "lab"):
        errors.extend(portfolio_link_errors(DIST / listing / "index.html"))

    sitemap = ET.parse(DIST / "sitemap.xml")
    urls = [node.text or "" for node in sitemap.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    routes = {urlsplit(url).path.rstrip("/") or "/" for url in urls}
    if len(urls) != len(routes):
        errors.append("Duplicate routes in sitemap")
    for route in routes:
        if not exists((DIST / route.lstrip("/")).resolve()):
            errors.append(f"Sitemap route has no page: {route}")
    for page in pages:
        if page.name == "404.html":
            continue
        route = "/" + str(page.relative_to(DIST).parent).strip(".").strip("/")
        if route not in routes:
            errors.append(f"Page missing from sitemap: {route}")
    if not (DIST / "404.html").is_file():
        errors.append("Missing custom 404 page")
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"Validated {len(pages)} HTML files, {len(urls)} sitemap URLs and all local HTML/CSS references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

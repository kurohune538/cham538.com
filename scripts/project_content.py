"""Render the additional portfolio entries from their bilingual source content."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def paragraphs(items: list[str]) -> str:
    return "".join(f"<p>{esc(item)}</p>" for item in items)


def add_project_content(root: Path) -> None:
    dist = root / "dist"
    projects = json.loads((root / "content/projects.json").read_text(encoding="utf-8"))
    template = (root / "content/project-template.html").read_text(encoding="utf-8")
    works = (dist / "works/index.html").read_text(encoding="utf-8")
    navigation = works.split("<body>", 1)[1].split('<div class="section4">', 1)[0]
    navigation = navigation.replace(' aria-current="page"', "").replace(' w--current"', '"')
    head = works.split("<head>", 1)[1].split("</head>", 1)[0]
    styles = re.findall(r"<link\b[^>]*>|<script\b[^>]*>.*?</script>", head, re.DOTALL)
    styles = [tag for tag in styles if 'rel="canonical"' not in tag]
    grid = '<div class="w-layout-grid grid">'
    cards: dict[str, list[str]] = {"works": [], "lab": []}
    sitemap_entries = []
    media = {"portfolio.css"}
    for project in projects:
        category = project["category"]
        section = "work" if category == "works" else "lab"
        route = f"/{section}/{project['slug']}"
        image = project["image"]
        media.add(image["file"])
        media.add(image.get("social_file", image["file"]))
        hero_media = (
            f'<img src="/assets/{esc(image["file"])}" width="{image["width"]}" '
            f'height="{image["height"]}" alt="{esc(image["alt"])}" fetchpriority="high"/>'
        )
        if "video" in project:
            video = project["video"]
            media.add(video["file"])
            hero_media = (
                f'<video controls playsinline preload="metadata" poster="/assets/{esc(image["file"])}" '
                f'width="{image["width"]}" height="{image["height"]}" '
                f'aria-label="{esc(video["label"])}">'
                f'<source src="/assets/{esc(video["file"])}" type="video/mp4"/>'
                f'<a href="/assets/{esc(video["file"])}">Watch the performance video</a></video>'
            )
        cards[category].append(
            f'<a href="{route}" class="w-inline-block portfolio-card">'
            f'<div class="text-block-21">{esc(project["kicker"])}</div>'
            f'<img src="/assets/{esc(image["file"])}" width="{image["width"]}" '
            f'height="{image["height"]}" alt="{esc(image["alt"])}" loading="lazy" '
            'class="image-13" style="width:100%;height:auto"/>'
            f'<div class="text-block-23">{esc(project["title"])}</div>'
            f'<div class="text-block-25">{esc(project["card"])}</div></a>'
        )
        facts = "".join(f'<div><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>'
                        for label, value in project["facts"])
        sections = []
        for index, item in enumerate(project["sections"], 1):
            steps = ""
            if "steps" in item:
                steps = '<ol class="portfolio-steps">' + "".join(
                    f'<li><h3>{esc(step[0])}</h3><p>{esc(step[1])}</p>'
                    f'<p lang="ja">{esc(step[2])}</p></li>' for step in item["steps"]
                ) + "</ol>"
            sections.append(
                f'<section class="portfolio-section" aria-labelledby="section-{index}">'
                f'<div class="portfolio-section-label"><span>{index:02d}</span>'
                f'<h2 id="section-{index}">{esc(item["heading"])}</h2></div>'
                f'<div class="portfolio-copy">{paragraphs(item.get("en", []))}{steps}'
                f'<div class="portfolio-translation" lang="ja">{paragraphs(item.get("ja", []))}</div>'
                '</div></section>'
            )
        links = "".join(f'<a href="{esc(url)}" class="portfolio-link">{esc(label)} ↗</a>'
                        for label, url in project.get("links", []))
        gallery = ""
        if "gallery" in project:
            photos = project["gallery"]
            is_collection = isinstance(photos, list)
            if not is_collection:
                photos = [photos]
            figures = []
            for photo in photos:
                media.add(photo["file"])
                figures.append(
                    f'<figure class="portfolio-gallery"><img src="/assets/{esc(photo["file"])}" '
                    f'width="{photo["width"]}" height="{photo["height"]}" '
                    f'alt="{esc(photo["alt"])}" loading="lazy"/>'
                    f'<figcaption>{esc(photo["caption"])}</figcaption></figure>'
                )
            gallery = "".join(figures)
            if is_collection:
                gallery_heading = esc(project.get("gallery_heading", "Exhibition photographs"))
                gallery_class = "portfolio-gallery-grid"
                if project.get("gallery_layout") == "wide":
                    gallery_class += " portfolio-gallery-grid-wide"
                gallery = (f'<section class="portfolio-documentation" aria-label="{gallery_heading}">'
                           f'<h2>{gallery_heading}</h2>'
                           f'<div class="{gallery_class}">{gallery}</div></section>')
        tokens = {
            "TITLE": esc(project["title"]), "DESCRIPTION": esc(project["summary"]),
            "ROUTE": route, "KICKER": esc(project["kicker"]),
            "DECK": esc(project["deck"]), "SUMMARY_JA": esc(project["summary_ja"]),
            "IMAGE": esc(image["file"]), "IMAGE_ALT": esc(image["alt"]),
            "IMAGE_WIDTH": str(image["width"]), "IMAGE_HEIGHT": str(image["height"]),
            "SOCIAL_IMAGE": esc(image.get("social_file", image["file"])),
            "CAPTION": esc(image["caption"]), "FACTS": facts,
            "HERO_MEDIA": hero_media,
            "SECTIONS": "\n".join(sections), "LINKS": links, "GALLERY": gallery,
            "CATEGORY": "Works" if category == "works" else "Lab",
            "CATEGORY_PATH": category, "SITE_NAVIGATION": navigation,
            "SITE_STYLES": "\n".join(styles),
        }
        page = template
        for token, value in tokens.items():
            page = page.replace(f"__{token}__", value)
        if re.search(r"__[A-Z_]+__", page):
            raise RuntimeError(f"Unresolved template token for {route}")
        target = dist / route.lstrip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
        sitemap_entries.append(f"    <url><loc>https://www.cham538.com{route}</loc></url>\n")
    for category, entries in cards.items():
        path = dist / category / "index.html"
        page = path.read_text(encoding="utf-8")
        if page.count(grid) != 1:
            raise RuntimeError(f"Expected exactly one {category} grid")
        path.write_text(page.replace(grid, grid + "\n".join(entries), 1), encoding="utf-8")
    for name in media:
        shutil.copyfile(root / "static" / name, dist / "assets" / name)
    sitemap_path = dist / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8")
    sitemap_path.write_text(sitemap.replace("</urlset>", "".join(sitemap_entries) + "</urlset>"), encoding="utf-8")

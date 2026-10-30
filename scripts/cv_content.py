"""Render the dated CV record into the existing portfolio pages."""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def rows(entries: list[dict], *, compact: bool = False) -> str:
    output = []
    for entry in entries:
        title = escape(entry["title"])
        if entry.get("url"):
            title = f'<a href="{escape(entry["url"])}">{title}</a>'
        date = f'<div class="cv-date">{escape(entry["date"])}</div>' if entry.get("date") else ""
        organization = f'<p class="cv-organization">{escape(entry["organization"])}</p>' if entry.get("organization") else ""
        detail = f'<p class="cv-detail">{escape(entry["detail"])}</p>' if entry.get("detail") and not compact else ""
        row_class = "cv-row" if date else "cv-row cv-row-undated"
        output.append(f'<li class="{row_class}">{date}<div><h3>{title}</h3>{organization}{detail}</div></li>')
    return '<ul class="cv-rows">' + "\n".join(output) + '</ul>'


def section(title: str, identifier: str, entries: list[dict], *, compact: bool = False) -> str:
    return (f'<section class="cv-section" id="{identifier}" aria-labelledby="{identifier}-title">'
            f'<h2 id="{identifier}-title">{title}</h2>{rows(entries, compact=compact)}</section>')


def download(data: dict, *, small: bool = False) -> str:
    style = "cv-download cv-download-small" if small else "cv-download"
    return (f'<a class="{style}" href="{escape(data["download"])}" download="Shinnosuke-Komiya-CV-2026.pdf">'
            'Download CV <span>PDF · 3 pages</span><span aria-hidden="true">↓</span></a>')


def apply_cv_content(root: Path) -> None:
    data = json.loads((root / "content/cv-2026.json").read_text(encoding="utf-8"))
    dist = root / "dist"
    source_pdf = root / "static/downloads/Shinnosuke-Komiya-CV-2026.pdf"
    target_pdf = dist / data["download"].lstrip("/")
    target_pdf.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_pdf, target_pdf)
    shutil.copyfile(root / "static/cv.css", dist / "assets/cv.css")

    # The new project pages reuse the Works navigation later in the build.
    blog = '<a href="https://note.com/kurohune538"'
    nav_link = (f'<a href="{escape(data["download"])}" download="Shinnosuke-Komiya-CV-2026.pdf" '
                'class="navigation-item w-nav-link" aria-label="Download CV (PDF)">CV ↓</a>')
    for path in dist.rglob("*.html"):
        content = path.read_text(encoding="utf-8")
        if blog in content:
            content = content.replace(blog, nav_link + blog, 1)
            path.write_text(content, encoding="utf-8")

    biography = ('I&#x27;m an artist, researcher, design engineer and educator working across '
                 'art, design and human–computer interaction.')
    old_biography = 'I&#x27;m an Art/Design Engineer / Human Computer Interaction researcher / Creative Technologist.'
    css = '<link rel="stylesheet" href="/assets/cv.css"/>'

    home_path = dist / "index.html"
    home = home_path.read_text(encoding="utf-8")
    home = home.replace(old_biography, biography)
    home = home.replace('Art/Design Engineer, HCI Researcher', 'Artist, Researcher, Design Engineer &amp; Educator')
    marker = '<div class="section4"><div class="w-container">'
    start = home.index(marker)
    end = home.index('<div class="footer-wrap">', start)
    bio_match = re.search(r'<p class="paragraph-3">.*?</p>', home[start:end], re.DOTALL)
    if not bio_match:
        raise RuntimeError("Expected the existing homepage biography")
    home_body = (
        '<main class="cv-home"><div class="cv-home-intro">' + bio_match.group(0)
        + f'<p class="cv-profile-copy">{escape(data["profile"])}</p>' + download(data)
        + '<p class="cv-source-date">CV 2026 · Updated ' + escape(data["updated"]) + '</p></div>'
        + section('Professional experience', 'experience', data["experience"])
        + section('Teaching &amp; advising', 'teaching', data["teaching"])
        + section('Education', 'education', data["education"])
        + '<p class="cv-more"><a href="/about#curriculum-vitae">Awards, residencies, presentations &amp; exhibitions →</a></p></main>'
    )
    home = home[:start] + home_body + home[end:]
    home_path.write_text(home.replace('</head>', css + '</head>', 1), encoding="utf-8")

    about_path = dist / "about/index.html"
    about = about_path.read_text(encoding="utf-8").replace(old_biography, biography)
    about = about.replace('</p>', '</p><div class="cv-intro-download">' + download(data, small=True) + '</div>', 1)
    start = about.index('<div class="section4"><div class="container3"><div class="w-layout-grid personal-features-grid">')
    end = about.index('<div class="footer-wrap">', start)
    categories = [
        ('Experience', 'experience'), ('Education', 'education'), ('Teaching &amp; advising', 'teaching'),
        ('Awards', 'awards'), ('Residencies', 'residencies'), ('Presentations', 'presentations'),
        ('Exhibitions &amp; performances', 'exhibitions'), ('Representative works', 'works'),
        ('Skills &amp; qualifications', 'qualifications'),
    ]
    links = ''.join(f'<a href="#cv-{key}">{title}</a>' for title, key in categories)
    full_cv = (
        '<main class="cv-page" id="curriculum-vitae"><header class="cv-header">'
        '<div><p class="cv-kicker">Shinnosuke Komiya / Yamico</p><h2>Curriculum vitae</h2>'
        f'<p class="cv-profile-copy">{escape(data["profile"])}</p>'
        f'<p class="cv-source-date">CV 2026 · Updated {escape(data["updated"])}</p></div>{download(data)}</header>'
        f'<nav class="cv-jump-links" aria-label="CV sections">{links}</nav>'
        + ''.join(section(title, 'cv-' + key, data[key]) for title, key in categories)
        + '<p class="cv-contact"><a href="mailto:kurohune538@gmail.com">kurohune538@gmail.com</a>'
        ' · <a href="https://github.com/kurohune538">GitHub</a>'
        ' · <a href="https://www.linkedin.com/in/shinnosuke-komiya-21482189/">LinkedIn</a></p></main>'
    )
    about = about[:start] + full_cv + about[end:]
    about_path.write_text(about.replace('</head>', css + '</head>', 1), encoding="utf-8")

    appearances_path = dist / "appearances-news/index.html"
    appearances = appearances_path.read_text(encoding="utf-8")
    updates = [data["presentations"][0], data["awards"][0], *data["exhibitions"][:3],
               data["presentations"][1], data["residencies"][0], data["exhibitions"][3]]
    grid = '<div class="cards-grid-container">'
    if appearances.count(grid) != 1:
        raise RuntimeError("Expected one Appearances archive grid")
    additions = (
        '<section class="cv-history" aria-labelledby="cv-history-title"><h3 id="cv-history-title">Talks, residencies &amp; performances</h3>'
        + rows(updates) + '</section><h3 class="cv-archive-title">More appearances</h3>'
    )
    appearances = appearances.replace(grid, additions + grid, 1)
    appearances = appearances.replace('I presented an oral presentation about prototype of GROOVE.',
        'Presented “A new outdoor activity utilizing smartphone and insole device” at ADADA Japan 2015.', 1)
    appearances_path.write_text(appearances.replace('</head>', css + '</head>', 1), encoding="utf-8")

    audit = {
        'cv_updated': data['updated'], 'download': data['download'],
        'source_pdf_sha256': hashlib.sha256(source_pdf.read_bytes()).hexdigest(),
        'categories': {key: len(data[key]) for _, key in categories},
        'appearances_added': len(updates),
        'notes': ['The original PDF is served unchanged.',
                  'The website uses the dated employment table rather than the older Eukarya sentence in the PDF biography.',
                  'Existing awards and the teaching-assistant entry are retained.',
                  'The dated six-year skills statement is paraphrased without presenting a stale duration as a current total.'],
    }
    (root / '.local/audit/cv-sync.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

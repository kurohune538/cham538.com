#!/usr/bin/env python3
"""Build a local, Webflow-independent static mirror from captured public HTML."""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "original-pages"
DIST = ROOT / "dist"
AUDIT = ROOT / ".local" / "audit"
STATIC = ROOT / "static"
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"

# Adobe Fonts Web Project confirmed in the owner's logged-in Adobe account.
# This is Adobe's current embed for the existing cham538.com project; no font
# binaries are copied or self-hosted.
ADOBE_FONTS_EMBED = """<script>
  (function(d) {
    var config = {
      kitId: 'snk6gsd',
      scriptTimeout: 3000,
      async: true
    },
    h=d.documentElement,t=setTimeout(function(){h.className=h.className.replace(/\\bwf-loading\\b/g,"")+" wf-inactive";},config.scriptTimeout),tk=d.createElement("script"),f=false,s=d.getElementsByTagName("script")[0],a;h.className+=" wf-loading";tk.src='https://use.typekit.net/'+config.kitId+'.js';tk.async=true;tk.onload=tk.onreadystatechange=function(){a=this.readyState;if(f||a&&a!="complete"&&a!="loaded")return;f=true;clearTimeout(t);try{Typekit.load(config)}catch(e){}};s.parentNode.insertBefore(tk,s)
  })(document);
</script>"""

PAGES = {
    "index.html": "index.html",
    "about.html": "about/index.html",
    "appearances-news.html": "appearances-news/index.html",
    "works.html": "works/index.html",
    "lab.html": "lab/index.html",
    "work-groove.html": "work/groove/index.html",
    "work-actput-old.html": "work/actput-old/index.html",
    "work-petapeta.html": "work/petapeta/index.html",
    "work-smartcane.html": "work/smartcane/index.html",
    "work-actput.html": "work/actput/index.html",
    "work-epitaph-of-the-earth.html": "work/epitaph-of-the-earth/index.html",
}

CANONICALS = {
    "index.html": "https://www.cham538.com/",
    "about.html": "https://www.cham538.com/about",
    "appearances-news.html": "https://www.cham538.com/appearances-news",
    "works.html": "https://www.cham538.com/works",
    "lab.html": "https://www.cham538.com/lab",
    "work-groove.html": "https://www.cham538.com/work/groove",
    "work-actput-old.html": "https://www.cham538.com/work/actput-old",
    "work-petapeta.html": "https://www.cham538.com/work/petapeta",
    "work-smartcane.html": "https://www.cham538.com/work/smartcane",
    "work-actput.html": "https://www.cham538.com/work/actput",
    "work-epitaph-of-the-earth.html": "https://www.cham538.com/work/epitaph-of-the-earth",
}

CDN_RE = re.compile(
    r"https://cdn\.prod\.website-files\.com/5daf4a741c624d69ae5be498/"
    r"[^\"'<>\s,]+"
)
CSS_ASSET_RE = re.compile(
    r"https://(?:cdn\.prod\.website-files\.com/5daf4a741c624d69ae5be498|"
    r"d3e54v103j8qbb\.cloudfront\.net)/(?:img|static)?/?[^\"'<>\s,)]+"
)


def local_name(url: str) -> str:
    path = unquote(urlsplit(html.unescape(url)).path)
    basename = Path(path).name or "asset"
    basename = re.sub(r"[^A-Za-z0-9._-]+", "-", basename).strip("-") or "asset"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{digest}-{basename}"


def collect_assets() -> dict[str, str]:
    assets: dict[str, str] = {}
    for source_name in PAGES:
        content = (SOURCE / source_name).read_text(encoding="utf-8")
        for match in CDN_RE.findall(content):
            url = html.unescape(match)
            if "/js/" in url:
                continue
            assets[url] = f"/assets/{local_name(url)}"
    return dict(sorted(assets.items()))


def remove_vendor_scripts(content: str) -> str:
    # The static build has no runtime dependency on Webflow's asset origin.
    content = re.sub(
        r'<link href="https://cdn\.prod\.website-files\.com" rel="preconnect"[^>]*/>',
        "",
        content,
    )

    external_patterns = (
        r"<script[^>]+src=\"https://ajax\.googleapis\.com/ajax/libs/webfont/[^\"]+\"[^>]*></script>",
        r"<script[^>]+src=\"https://use\.typekit\.net/[^\"]+\"[^>]*></script>",
        r"<script[^>]+src=\"https://www\.googletagmanager\.com/[^\"]+\"[^>]*></script>",
        r"<script[^>]+src=\"https://d3e54v103j8qbb\.cloudfront\.net/js/jquery-[^\"]+\"[^>]*></script>",
        r"<script[^>]+src=\"https://cdn\.prod\.website-files\.com/[^\"]+/js/webflow\.[^\"]+\"[^>]*></script>",
    )
    for pattern in external_patterns:
        content = re.sub(pattern, "", content)

    inline_patterns = (
        r"<script[^>]*>WebFont\.load\(.*?</script>",
        r"<script[^>]*>try\{Typekit\.load\(\);\}catch\(e\)\{\}</script>",
        r"<script[^>]*>!function\(o,c\).*?</script>",
        r"<script[^>]*>window\.dataLayer = window\.dataLayer.*?</script>",
    )
    for pattern in inline_patterns:
        content = re.sub(pattern, "", content, flags=re.DOTALL)
    return content


def rewrite_page(source_name: str, target_name: str, assets: dict[str, str]) -> None:
    content = (SOURCE / source_name).read_text(encoding="utf-8")
    content = remove_vendor_scripts(content)

    # The owner decided not to migrate the Webflow contact form. Remove the
    # complete section instead of leaving a disabled form or hidden controls.
    if source_name == "about.html":
        content, removed = re.subn(
            r'<div class="section4 cc-contact">.*?(?=<div class="footer-wrap">)',
            "",
            content,
            count=1,
            flags=re.DOTALL,
        )
        if removed != 1:
            raise RuntimeError("Expected exactly one About contact section")

    # Webflow stored five IX2 initial states inline. The native interaction
    # replacement applies those states at runtime; removing them here keeps
    # the content visible when JavaScript is unavailable.
    content = content.replace(' style="opacity:0"', "")

    for url, local in sorted(assets.items(), key=lambda item: len(item[0]), reverse=True):
        content = content.replace(url, local)
        content = content.replace(url.replace("&", "&amp;"), local)

    # Make third-party embeds explicit instead of inheriting the page protocol.
    content = content.replace('src="//', 'src="https://')
    content = content.replace('href="//', 'href="https://')

    # Local files do not need remote integrity/CORS attributes.
    content = re.sub(
        r'(<link href="/assets/[^"]+\.css" rel="stylesheet" type="text/css")'
        r' integrity="[^"]+" crossorigin="anonymous"',
        r"\1",
        content,
    )

    canonical = CANONICALS[source_name]
    font_link = (
        '<link rel="preconnect" href="https://fonts.googleapis.com"/>'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous"/>'
        '<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=Ubuntu:ital,wght@0,300;0,400;0,500;0,700;1,300;1,400;1,500;1,700&display=swap" rel="stylesheet"/>'
    )
    additions = (
        f'<link rel="canonical" href="{canonical}"/>'
        f"{font_link}"
        f"{ADOBE_FONTS_EMBED}"
        '<link href="/assets/local-overrides.css" rel="stylesheet" type="text/css"/>'
    )
    content = content.replace("</head>", f"{additions}</head>", 1)
    content = content.replace("</body>", '<script src="/assets/site.js"></script></body>', 1)

    # Keep social images absolute for the eventual cham538.com cutover.
    content = re.sub(
        r'content="/assets/([^"]+)" (property="og:image"|name="twitter:image")',
        r'content="https://www.cham538.com/assets/\1" \2',
        content,
    )

    target = DIST / target_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def load_existing_css_extras() -> dict[str, str]:
    """Keep CSS-only asset mappings reproducible after CSS has been localized."""
    config = ROOT / "config" / "css-assets.json"
    urls = json.loads(config.read_text(encoding="utf-8"))
    return {url: f"/assets/{local_name(url)}" for url in urls}


def localize_downloaded_css(assets: dict[str, str]) -> dict[str, str]:
    extras: dict[str, str] = load_existing_css_extras()
    for local in list(assets.values()):
        if not local.endswith(".css"):
            continue
        css_path = DIST / local.lstrip("/")
        if not css_path.exists():
            continue
        content = css_path.read_text(encoding="utf-8")
        for url in CSS_ASSET_RE.findall(content):
            if url not in assets:
                extras[url] = f"/assets/{local_name(url)}"
        for url, local_path in {**assets, **extras}.items():
            content = content.replace(url, local_path)
        css_path.write_text(content, encoding="utf-8")
    return extras


def write_download_config(assets: dict[str, str], filename: str) -> None:
    lines = ["location", "fail", "silent", "show-error", "create-dirs"]
    for url, local in assets.items():
        rel_path = f"dist{local}"
        escaped_url = url.replace('"', r'\"')
        escaped_path = rel_path.replace('"', r'\"')
        lines.extend([f'url = "{escaped_url}"', f'output = "{escaped_path}"'])
    (AUDIT / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_content_audit() -> None:
    pages = []
    external_links = []
    for source_name, target_name in PAGES.items():
        content = (SOURCE / source_name).read_text(encoding="utf-8")
        title_match = re.search(r"<title>(.*?)</title>", content, re.I | re.S)
        description_match = re.search(
            r'<meta[^>]+(?:name="description"[^>]+content="([^"]*)"|'
            r'content="([^"]*)"[^>]+name="description")',
            content,
            re.I,
        )
        description = ""
        if description_match:
            description = next(
                (value for value in description_match.groups() if value is not None),
                "",
            )
        outbound = []
        for kind, pattern in (
            ("link", r'<a\b[^>]*href="([^"]+)"'),
            ("iframe", r'<iframe\b[^>]*src="([^"]+)"'),
            ("form", r'<form\b[^>]*action="([^"]+)"'),
        ):
            for value in re.findall(pattern, content, re.I):
                decoded = html.unescape(value)
                if decoded.startswith("//"):
                    decoded = "https:" + decoded
                if urlsplit(decoded).scheme in {"http", "https"}:
                    outbound.append((kind, decoded))
        page_external = sorted(set(outbound))
        external_links.extend(
            {"page": CANONICALS[source_name], "kind": kind, "url": value}
            for kind, value in page_external
        )
        pages.append(
            {
                "url": CANONICALS[source_name],
                "local": "/" + str(Path(target_name).parent).replace(".", "").strip("/"),
                "title": html.unescape(title_match.group(1)).strip() if title_match else "",
                "description": html.unescape(description),
                "images": len(re.findall(r"<img\b", content, re.I)),
                "iframes": len(re.findall(r"<iframe\b", content, re.I)),
                "forms": len(re.findall(r"<form\b", content, re.I)),
                "webflow_interaction_ids": len(re.findall(r"data-w-id=", content)),
                "webflow_dynamic_lists": len(re.findall(r"w-dyn-list", content)),
                "placeholder_links": len(re.findall(r'href="(?:#)?"', content, re.I)),
                "external_urls": len(page_external),
            }
        )
    (AUDIT / "page-inventory.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (AUDIT / "external-links.json").write_text(
        json.dumps(external_links, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def add_portfolio_projects() -> None:
    """Layer new portfolio content onto the preserved Webflow export."""
    works_path = DIST / "works/index.html"
    works = works_path.read_text(encoding="utf-8")
    grid = '<div class="w-layout-grid grid">'
    if works.count(grid) != 1:
        raise RuntimeError("Expected one Works grid for the new project card")
    projects = ("read-between-you", "cascade", "epitaph-of-the-earth")
    card = "".join((CONTENT / f"{slug}-card.html").read_text(encoding="utf-8") for slug in projects)
    works_path.write_text(works.replace(grid, grid + card, 1), encoding="utf-8")

    # Reuse the current site's actual navigation and font/style embeds.
    navigation = works.split("<body>", 1)[1].split('<div class="section4">', 1)[0]
    navigation = navigation.replace(' aria-current="page"', "")
    navigation = navigation.replace(' w--current"', '"')
    head = works.split("<head>", 1)[1].split("</head>", 1)[0]
    styles = re.findall(r"<link\b[^>]*>|<script\b[^>]*>.*?</script>", head, re.DOTALL)
    styles = [tag for tag in styles if 'rel="canonical"' not in tag]
    if not any("local-overrides.css" in tag for tag in styles):
        raise RuntimeError("Expected the current site's styles in the project page")
    for slug in projects:
        page = (CONTENT / f"{slug}.html").read_text(encoding="utf-8")
        page = page.replace("__SITE_NAVIGATION__", navigation)
        page = page.replace("__SITE_STYLES__", "\n".join(styles))
        target = DIST / f"work/{slug}/index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
    for name in ("read-between-you-key-visual.jpg", "read-between-you.css",
                 "epitaph-installation.jpg", "epitaph-placement.jpg", "epitaph-of-the-earth.css",
                 "cascade-key-visual.jpg", "cascade.css"):
        shutil.copyfile(STATIC / name, DIST / "assets" / name)

    sitemap_path = DIST / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8")
    entry = "".join(f"    <url><loc>https://www.cham538.com/work/{slug}</loc></url>\n"
                    for slug in projects if f"work-{slug}.html" not in PAGES)
    sitemap_path.write_text(sitemap.replace("</urlset>", entry + "</urlset>"), encoding="utf-8")


def main() -> None:
    # dist is generated output. Recreate it so deleted pages cannot linger.
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    # All downloadable assets are bundled in Git; builds need no network.
    shutil.copytree(ASSETS, DIST / "assets")
    shutil.copyfile(STATIC / "site.js", DIST / "assets" / "site.js")
    shutil.copyfile(
        STATIC / "local-overrides.css",
        DIST / "assets" / "local-overrides.css",
    )
    shutil.copyfile(STATIC / "_headers", DIST / "_headers")
    not_found = (STATIC / "404.html").read_text(encoding="utf-8")
    not_found = not_found.replace(
        "</head>", f"{ADOBE_FONTS_EMBED}</head>", 1
    )
    (DIST / "404.html").write_text(not_found, encoding="utf-8")
    assets = collect_assets()
    for source_name, target_name in PAGES.items():
        rewrite_page(source_name, target_name, assets)

    favicon_url = (
        "https://cdn.prod.website-files.com/5daf4a741c624d69ae5be498/"
        "60afe8d6c81d5506b34010b9_favicon%20(1).ico"
    )
    favicon_asset = DIST / assets[favicon_url].lstrip("/")
    if favicon_asset.exists():
        shutil.copyfile(favicon_asset, DIST / "favicon.ico")

    shutil.copyfile(SOURCE / "robots.txt", DIST / "robots.txt")
    shutil.copyfile(SOURCE / "sitemap.xml", DIST / "sitemap.xml")
    add_portfolio_projects()
    write_download_config(assets, "curl-assets.conf")
    css_extras = localize_downloaded_css(assets)
    if css_extras:
        write_download_config(css_extras, "curl-css-assets.conf")
        assets.update(css_extras)
    (AUDIT / "asset-manifest.json").write_text(
        json.dumps(
            [{"source": url, "local": local} for url, local in assets.items()],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_content_audit()
    print(f"Prepared {len(list(DIST.rglob('index.html')))} pages and {len(assets)} downloadable assets, plus project media.")


if __name__ == "__main__":
    main()

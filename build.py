#!/usr/bin/env python3
"""Builds ashvienjitan.nl into dist/.

    python3 build.py

Sermons (YouTube), books (Faith Generation webshop) and the agenda are fetched
fresh on every build; see sources.py. No third-party packages needed.
"""
import datetime as dt
import json
import os
import re
import shutil
from zoneinfo import ZoneInfo
from html import escape
from pathlib import Path

import sources

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
# Path prefix when the site is served from a subfolder (e.g. username.github.io/repo).
# Empty once the site runs on its own domain.
BASE = os.environ.get("SITE_BASE", "").rstrip("/")
# Absolute address of the site, for canonical links, social previews and the sitemap.
SITE_URL = os.environ.get("SITE_URL", "https://ashvienjitan.nl").rstrip("/")

FG = "https://faithgeneration.com"
LINKS = {
    "invite": f"{FG}/spreekverzoeken/",
    "give": f"{FG}/geven/",
    "give_partner": f"{FG}/geven/",
    "give_truck": f"{FG}/activiteiten/gospeltrucks/",
    "give_big": f"{FG}/geven/doe-een-grote-schenking/",
    "contact": f"{FG}/contact/",
    "jesus": f"{FG}/ik-wil-de-here-jezus-leren-kennen/",
    "shop": f"{FG}/shop/",
    "agenda": f"{FG}/agenda/",
    "podcast": f"{FG}/podcast/",
    "teachings": f"{FG}/faith-teaching/",
    "bibleschool": "https://faithgenerationschool.nl",
    "youtube": "https://www.youtube.com/channel/UCHLfXcDbVr49nuHQLh_TMYA",
    "instagram": "https://www.instagram.com/faithgeneration/",
    "facebook": "https://www.facebook.com/faithgeneration.ministry/",
    "newsletter": f"{FG}/",
    "privacy": f"{FG}/privacyverklaring/",
    "testimonies": f"{FG}/getuigenissen/",
    "anbi": f"{FG}/anbi-status/",
}

# Homepage reel. Add `"video": "/video/xyz.mp4"` to a slide once the clip exists;
# the photo then becomes its poster frame.
HERO_SLIDES = [
    {"label": "Prediking", "img": "/img/hero.jpg"},
    {"label": "Gebed", "img": "/img/genezing.jpg"},
    {"label": "Gospeltruck", "img": "/img/gospeltruck-india.jpg"},
    {"label": "Bijbelschool", "img": "/img/onderwijs.jpg"},
]

BOOK_CATEGORIES = {
    "genezing": ("genezing", "genees", "gezondheid", "avondmaal"),
    "gebed": ("bidden", "stille tijd", "tongentaal", "vasten", "gods stem"),
    "groei": ("basics", "nieuw leven", "bijbel", "visie", "koninkrijk", "manifestaties",
              "geestelijke strijd", "bevrijding", "armoede"),
    "evangelisatie": ("evangelie", "nog niet gelovige"),
}

MONTHS_NL = ["JAN", "FEB", "MRT", "APR", "MEI", "JUN", "JUL", "AUG", "SEP", "OKT", "NOV", "DEC"]

ICON = {
    "arrow-up-right": '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "play": '<polygon points="6 3 20 12 6 21 6 3" fill="currentColor"/>',
    "menu": '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "minus": '<path d="M5 12h14"/>',
    "refresh": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    "youtube": '<path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17"/><path d="m10 15 5-3-5-3z"/>',
    "instagram": '<rect width="20" height="20" x="2" y="2" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>',
    "facebook": '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
}


def icon(name, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>')


def e(s):
    return escape(str(s), quote=True)


def ext(href):
    return ' target="_blank" rel="noopener"' if href.startswith("http") else ""


def nl_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {MONTHS_NL[d.month - 1]} {d.year}"


def yt_thumb(vid, size="hqdefault"):
    return f"https://i.ytimg.com/vi/{vid}/{size}.jpg"


# ---------- Shared chrome ----------

NAV = [("Over Ashvien", "/over-ashvien/"), ("Onderwijs", "/onderwijs/"), ("Webshop", "/webshop/"),
       ("Geven", LINKS["give"]), ("Contact", LINKS["contact"])]


def header(current, solid=False):
    links = "".join(
        f'<a href="{href}"{ext(href)}{" aria-current=page" if href == current else ""}>{e(label)}</a>'
        for label, href in NAV)
    return f'''<header class="site-header{' solid' if solid else ''}">
  <a class="logo" href="/" aria-label="Ashvien Jitan — home"><img src="/logo/aj-lockup-op-donker.svg" alt="Ashvien Jitan" width="246" height="64"></a>
  <nav class="nav" aria-label="Hoofdmenu">{links}
    <a class="btn btn-red" href="{LINKS['invite']}"{ext(LINKS['invite'])}>Nodig Ashvien uit {icon('arrow-up-right')}</a>
    <button class="menu-toggle" type="button" aria-label="Menu openen" aria-expanded="false" aria-controls="mobile-menu">{icon('menu')}</button>
  </nav>
</header>'''


def mobile_menu():
    items = [("Over Ashvien", "/over-ashvien/"),
             ("Onderwijs", [("Preken", "/onderwijs/#preken"), ("Faith Teachings", LINKS["teachings"]),
                            ("Podcast", LINKS["podcast"]), ("Bijbelscholen", LINKS["bibleschool"])]),
             ("Webshop", "/webshop/"), ("Agenda", "/#agenda"), ("Geven", LINKS["give"]), ("Contact", LINKS["contact"])]
    rows = []
    for n, (label, target) in enumerate(items, 1):
        num = f'<span class="t">{e(label)}</span>'
        if isinstance(target, list):
            sub = "".join(f'<li><a href="{h}"{ext(h)}>{e(l)} {icon("arrow-right")}</a></li>' for l, h in target)
            rows.append(f'<li><button class="mm-row" type="button" data-sub="mm-sub-{n}" aria-expanded="false">{num}'
                        f'{icon("plus", "i-plus")}{icon("minus", "i-minus")}</button>'
                        f'<ul class="mm-sub" id="mm-sub-{n}">{sub}</ul></li>')
        else:
            rows.append(f'<li><a class="mm-row" href="{target}"{ext(target)}>{num}{icon("arrow-up-right")}</a></li>')
    return f'''<div class="mobile-menu" id="mobile-menu" aria-hidden="true" role="dialog" aria-label="Menu">
  <div>
    <div class="bar"><a href="/"><img src="/logo/aj-lockup-op-donker.svg" alt="Ashvien Jitan"></a>
      <button class="menu-close" type="button" aria-label="Menu sluiten">{icon('x')}</button></div>
    <ul class="mm-list">{''.join(rows)}</ul>
  </div>
  <div class="mm-bottom">
    <a class="btn btn-red" href="{LINKS['invite']}"{ext(LINKS['invite'])}>Nodig Ashvien uit {icon('arrow-up-right')}</a>
    <a class="btn btn-ghost" href="{LINKS['jesus']}"{ext(LINKS['jesus'])}>Ik wil Jezus leren kennen</a>
    <div class="mm-social"><div class="icons">
      <a href="{LINKS['youtube']}" target="_blank" rel="noopener" aria-label="YouTube">{icon('youtube')}</a>
      <a href="{LINKS['instagram']}" target="_blank" rel="noopener" aria-label="Instagram">{icon('instagram')}</a>
      <a href="{LINKS['facebook']}" target="_blank" rel="noopener" aria-label="Facebook">{icon('facebook')}</a></div>
      <span>onderdeel van Faith Generation</span></div>
  </div>
</div>'''


def jesus_cta():
    return f'''<section class="jesus">
  <div><span class="label">De belangrijkste keuze van je leven</span>
    <h2 class="display">Ik wil de Here Jezus<br>leren kennen.</h2></div>
  <a class="btn btn-ink" href="{LINKS['jesus']}"{ext(LINKS['jesus'])}>Zet de eerste stap {icon('arrow-up-right')}</a>
</section>'''


def footer():
    def col(title, items):
        lis = "".join(f'<li><a href="{h}"{ext(h)}>{e(l)}</a></li>' for l, h in items)
        return f"<div><h4>{title}</h4><ul>{lis}</ul></div>"
    return f'''<footer class="site-footer">
  <div class="foot-top">
    <div class="foot-brand">
      <img src="/logo/aj-lockup-op-donker.svg" alt="Ashvien Jitan" width="246" height="64">
      <p>Ontvang nieuwe preken en boeken in je inbox via de nieuwsbrief van Faith Generation.</p>
      <a class="link" href="{LINKS['newsletter']}" target="_blank" rel="noopener">Schrijf je in {icon('arrow-up-right')}</a>
    </div>
    <div class="foot-cols">
      {col("Navigatie", [("Over Ashvien", "/over-ashvien/"), ("Onderwijs", "/onderwijs/"), ("Webshop", "/webshop/"),
                         ("Nodig Ashvien uit", LINKS["invite"]), ("Geven", LINKS["give"]), ("Contact", LINKS["contact"])])}
      {col("Onderwijs", [("Preken", "/onderwijs/#preken"), ("Faith Teachings", LINKS["teachings"]),
                         ("Podcast", LINKS["podcast"]), ("Bijbelscholen", LINKS["bibleschool"])])}
      {col("Volg Ashvien", [("YouTube", LINKS["youtube"]), ("Instagram", LINKS["instagram"]), ("Facebook", LINKS["facebook"])])}
    </div>
  </div>
  <p class="foot-mark" aria-hidden="true">ASHVIEN JITAN</p>
  <div class="foot-bottom">
    <span>© {dt.date.today().year} Ashvien Jitan · Onderdeel van Stichting Faith Generation</span>
    <span><a href="{LINKS['privacy']}" target="_blank" rel="noopener">Privacy</a> · <a href="{FG}" target="_blank" rel="noopener">faithgeneration.com</a></span>
  </div>
</footer>'''


def json_ld(data):
    body = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")  # never close the script tag early
    return f'<script type="application/ld+json">{body}</script>'


PERSON = {
    "@type": "Person", "@id": f"{SITE_URL}/#ashvien", "name": "Ashvien Jitan",
    "jobTitle": "Evangelist", "description": "Evangelist, spreker, schrijver en oprichter van Faith Generation.",
    "url": f"{SITE_URL}/", "image": f"{SITE_URL}/img/portret-prediking.jpg",
    "worksFor": {"@type": "Organization", "name": "Stichting Faith Generation", "url": FG},
    "sameAs": [LINKS["youtube"], LINKS["instagram"], LINKS["facebook"], FG],
}


def page(title, description, current, main, head_inside=False, schema=(), preload=None, noindex=False):
    url = f"{SITE_URL}{current}"
    ld = "".join(json_ld({"@context": "https://schema.org", **d}) for d in schema)
    pre = f'<link rel="preload" as="image" href="{preload}" fetchpriority="high">' if preload else ""
    return f'''<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
{'<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{url}">'}
<meta property="og:type" content="website">
<meta property="og:locale" content="nl_NL">
<meta property="og:site_name" content="Ashvien Jitan">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{SITE_URL}/img/hero.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b0b0b">
<link rel="icon" href="/logo/aj-favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/logo/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
{pre}{ld}
</head>
<body>
{'' if head_inside else header(current)}
{mobile_menu()}
<main>
{main}
</main>
{footer()}
<script src="/js/site.js" defer></script>
</body>
</html>
'''


# ---------- Reusable blocks ----------

def eyebrow(label):
    return f'<p class="eyebrow label red">{label}</p>'


def sermon_block(sermons, list_count=4):
    if not sermons:
        return f'<p class="empty">Bekijk alle preken op <a class="link" href="{LINKS["youtube"]}">YouTube</a>.</p>'
    # Prefer a full service as the featured video; fall back to the newest upload.
    featured = next((s for s in sermons if sources.sermon_kind(s["title"]) in ("Genezingsdienst", "Healing Night")), sermons[0])
    rest = [s for s in sermons if s is not featured][:list_count]
    items = "".join(f'''<li><a href="https://www.youtube.com/watch?v={s['id']}" target="_blank" rel="noopener">
      <img src="{yt_thumb(s['id'], 'mqdefault')}" alt="" loading="lazy" width="320" height="180">
      <div><p class="small-label mute meta">{nl_date(s['date'])} · {e(sources.sermon_kind(s['title']))}</p>
      <h4>{e(sources.clean_title(s['title']))}</h4></div></a></li>''' for s in rest)
    return f'''<div class="sermons">
    <div class="featured">
      <a class="video" data-id="{featured['id']}" href="https://www.youtube.com/watch?v={featured['id']}" aria-label="Speel af: {e(featured['title'])}"
         style="background-image:url('{yt_thumb(featured['id'], 'maxresdefault')}'), url('{yt_thumb(featured['id'])}')">
        <span class="play">{icon('play')}</span></a>
      <div class="featured-meta"><span class="small-label badge">{"Nieuwste" if featured is sermons[0] else "Uitgelicht"}</span>
        <span class="small-label mute">{nl_date(featured['date'])} · {e(sources.sermon_kind(featured['title']))}</span></div>
      <h3>{e(sources.clean_title(featured['title']))}</h3>
    </div>
    <div><ul class="sermon-list">{items}</ul>
      <p style="margin-top:28px"><a class="link" href="{LINKS['youtube']}" target="_blank" rel="noopener">Alle preken op YouTube {icon('arrow-up-right')}</a></p></div>
  </div>
  <p class="auto-note">{icon('refresh')} Wordt automatisch bijgewerkt vanuit het YouTube-kanaal van Faith Generation</p>'''


def book_cards(books, eager=0):
    cards = []
    for i, b in enumerate(books):
        t = b["title"].lower()
        cats = " ".join(c for c, keys in BOOK_CATEGORIES.items() if any(k in t for k in keys))
        num = f"Boek {b['num']:02d}" if b["num"] else "Boek"
        cover = ""
        if b["cover"]:
            src, srcset = e(b["cover"]), ""
            if b["cover"].endswith(".png"):  # WooCommerce square thumbnails exist for the 3D mock-ups
                base = b["cover"][:-4]
                srcset = (f' srcset="{e(base)}-300x300.png 300w, {e(base)}-600x600.png 600w, {src} 1080w"'
                          f' sizes="(max-width: 760px) 45vw, 22vw" onerror="this.removeAttribute(\'srcset\')"')
            cover = f'<img src="{src}"{srcset} alt="Omslag: {e(b["title"])}" loading="{"eager" if i < eager else "lazy"}" width="300" height="300">'
        cards.append(f'''<a class="book" href="{e(b['url'])}" target="_blank" rel="noopener" data-cat="{cats}">
      <div class="cover">{cover}</div>
      <div class="meta small-label"><span class="mute">{num}</span><span class="red">{e(b['price'])}</span></div>
      <h3>{e(b['title'])}</h3>
      <span class="order">Bestel gratis {icon('arrow-up-right')}</span></a>''')
    return "".join(cards)


def package_banner(books):
    pkg = next((b for b in books if "pakket" in b["title"].lower()), None)
    href = pkg["url"] if pkg else LINKS["shop"]
    return f'''<div class="package"><div><h3>Boekpakket — boek 1 t/m 20</h3>
    <p class="mute">Alle twintig Nederlandse boeken in één pakket.</p></div>
    <a class="btn btn-red" href="{e(href)}" target="_blank" rel="noopener">Naar de webshop {icon('arrow-up-right')}</a></div>'''


def agenda_block(events, limit=None):
    if not events:
        return f'<p class="empty">Er staan op dit moment geen diensten gepland. Bekijk de <a class="link" href="{LINKS["agenda"]}">agenda van Faith Generation</a>.</p>'
    rows = []
    for ev in events[:limit]:
        times = " · ".join(t for t, _ in ev["sessions"])
        tag = next((l for _, l in ev["sessions"] if l), "Ticket" if ev["ticket"] else "Dienst")
        city = ev["place"].split(",")[-1].strip() if ev["place"] else ""
        href = ev["ticket"] or LINKS["agenda"]
        rows.append(f'''<li><a href="{e(href)}" target="_blank" rel="noopener">
      <div class="ev-date"><b>{e(ev['day'])}</b><span>{e(ev['month'])}</span></div>
      <div class="ev-info"><h3 class="ev-title">{e(ev['title'])}</h3><p class="mute">{e(city)}{'  ·  ' if city else ''}{e(times)}</p></div>
      <span class="ev-tag small-label">{e(tag)}</span>
      <span class="ev-go">{icon('arrow-up-right')}</span></a></li>''')
    return f'<ul class="events">{"".join(rows)}</ul>'


# ---------- Pages ----------

def event_schema(events):
    out = []
    for ev in events:
        if not ev.get("first"):
            continue
        times = [m.group(0) for t, _ in ev["sessions"] if (m := re.search(r"\d{1,2}:\d{2}", t))]
        start = ev["first"]
        if times:
            h, m = map(int, times[0].split(":"))
            start = dt.datetime.combine(dt.date.fromisoformat(ev["first"]), dt.time(h, m),
                                        ZoneInfo("Europe/Amsterdam")).isoformat()
        out.append({"@type": "Event", "name": f'{ev["title"]} met Ashvien Jitan', "startDate": start,
                    "endDate": ev.get("last") or ev["first"],
                    "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                    "eventStatus": "https://schema.org/EventScheduled",
                    "location": {"@type": "Place", "name": ev["title"], "address": ev["place"] or ev["title"]},
                    "performer": {"@id": f"{SITE_URL}/#ashvien"},
                    "organizer": {"@type": "Organization", "name": "Stichting Faith Generation", "url": FG},
                    "url": ev["ticket"] or LINKS["agenda"]})
    return out


def home(sermons, books, events):
    slides = "".join(
        (f'<video src="{s["video"]}" poster="{s["img"]}" muted playsinline loop preload="none"></video>' if s.get("video")
         else f'<img src="{s["img"]}" alt="" {"fetchpriority=high" if i == 0 else "loading=lazy"}>')
        for i, s in enumerate(HERO_SLIDES))
    reel = "".join(f'<button type="button"{" class=active" if i == 0 else ""}>{i + 1:02d} {e(s["label"])}</button>'
                   for i, s in enumerate(HERO_SLIDES))
    words = ["Bijbelscholen", "Wonderen &amp; genezingen", "20 boeken", "Gospeltrucks India", "Simpel onderwijs"]
    marquee = "".join(f"<span>{w.upper()}</span>" for w in words * 2)
    shop_books = [b for b in books if b["num"] in (1, 6, 13, 16)] or [b for b in books if b["num"]][:4]
    main = f'''
<section class="hero">
  <div class="hero-media" aria-hidden="true">{slides}</div>
  <div class="hero-content">
    <p class="tag">Evangelist · Spreker · Schrijver<span class="tag-more"> · Oprichter Faith Generation</span></p>
    <h1 class="display h-xl">Reviving a<br>generation of faith</h1>
    <p class="hero-sub">Simpel Bijbelonderwijs, gratis boeken en diensten waarin mensen genezing ervaren.</p>
    <div class="hero-foot">
      <div class="hero-buttons">
        <a class="btn btn-paper" href="/onderwijs/#preken">{icon('play')} Bekijk de laatste preek</a>
        <a class="btn btn-ghost" href="{LINKS['jesus']}"{ext(LINKS['jesus'])}>Ik wil Jezus leren kennen</a>
      </div>
      <div class="reel" aria-label="Beelden">{reel}</div>
    </div>
  </div>
</section>
<div class="marquee" aria-hidden="true"><div class="marquee-track">{marquee}</div></div>

<section class="section light">
  <div class="section-head"><h2 class="display h-lg">Een generatie<br>van geloof opwekken.</h2>{eyebrow('Over Ashvien')}</div>
  <div class="about-grid">
    <img class="photo" src="/img/portret-prediking.jpg" alt="Evangelist Ashvien Jitan preekt achter een kansel" loading="lazy" width="1280" height="1920">
    <div class="about-text">
      <p class="lead">Ashvien Jitan is evangelist, spreker, schrijver en de oprichter van Faith Generation. Zijn missie is eenvoudig: een generatie van geloof opwekken.</p>
      <p class="body">Met een heldere en simpele manier van onderwijs geven helpt hij mensen om het Woord van God te begrijpen en toe te passen in hun dagelijks leven. Ashvien staat bekend om zijn passie voor de Here Jezus en de wonderen en genezingen die regelmatig plaatsvinden tijdens zijn diensten.</p>
      <p class="body">Hij schreef twintig boeken, leidt Bijbelscholen in verschillende landen en bereikt maandelijks honderdduizenden mensen via evangelisatieprojecten wereldwijd. Vooral in India, waar tientallen gospeltrucks bijna dagelijks het evangelie delen.</p>
      <div class="stats">
        <div class="stat"><b>20</b><span>Boeken geschreven</span></div>
        <div class="stat"><b>14</b><span>Talen vertaald</span></div>
        <div class="stat"><b>40</b><span>Gospeltrucks in India</span></div>
        <div class="stat"><b class="red">200K+</b><span>Keuzes voor Jezus per maand, via de gospeltrucks</span></div>
      </div>
      <p><a class="link" href="/over-ashvien/">Lees het hele verhaal {icon('arrow-right')}</a></p>
    </div>
  </div>
</section>

<section class="section dark" id="onderwijs">
  <div class="section-head"><div><h2 class="display h-lg">Elke week<br>nieuwe preken.</h2></div>
    <nav class="tabs" aria-label="Onderwijs">
      <a class="active" href="/onderwijs/#preken">Preken</a><a href="{LINKS['teachings']}"{ext(LINKS['teachings'])}>Faith Teachings</a>
      <a href="{LINKS['podcast']}"{ext(LINKS['podcast'])}>Podcast</a><a href="{LINKS['bibleschool']}"{ext(LINKS['bibleschool'])}>Bijbelscholen</a></nav></div>
  {sermon_block(sermons)}
</section>

<section class="section light">
  <div class="section-head"><div><h2 class="display h-lg">20 boeken.<br>Gratis voor iedereen.</h2></div>
    <p class="aside body">De boeken worden vertaald in veertien talen en wereldwijd gratis uitgedeeld. Bestel ze direct via de webshop van Faith Generation.</p></div>
  <div class="books">{book_cards(shop_books)}</div>
  {package_banner(books)}
</section>

<section class="band" style="background-image:url('/img/gospeltruck-india.jpg')">
  <div class="band-inner">
    <div>{eyebrow('Gospeltrucks India')}<h2 class="display h-lg">40 trucks.<br>Elke dag het evangelie.</h2></div>
    <div class="stat-big"><b>200.000 – 250.000</b><p>mensen per maand kiezen voor de Here Jezus en worden direct verbonden met een lokale kerk.</p>
      <p style="margin-top:20px"><a class="link" href="{LINKS['testimonies']}" target="_blank" rel="noopener">Lees getuigenissen {icon('arrow-up-right')}</a></p></div>
  </div>
</section>

<section class="section dark" id="agenda">
  <div class="section-head"><div>{eyebrow('Agenda')}<h2 class="display h-lg">Kom langs.</h2></div>
    <a class="link" href="{LINKS['agenda']}" target="_blank" rel="noopener">Volledige agenda {icon('arrow-up-right')}</a></div>
  {agenda_block(events, limit=6)}
</section>

<section class="section light">
  <div class="split">
    <div class="card card-photo" style="background-image:url('/img/genezing.jpg')">
      <span class="label red">Nodig Ashvien uit</span>
      <h2 class="display h-md">Een genezingsdienst,<br>seminar of conferentie?</h2>
      <p class="body">Ashvien spreekt in kerken, op conferenties en evangelisatie-events in binnen- en buitenland.</p>
      <p class="body">Ashvien staat onder overzienerschap van pastor Jaap Dieleman.</p>
      <ul class="formats"><li>Genezingsdiensten</li><li>Seminars &amp; trainingen</li><li>Conferenties</li><li>Revival-weekenden</li></ul>
      <p><a class="btn btn-red" href="{LINKS['invite']}"{ext(LINKS['invite'])}>Spreekverzoek indienen {icon('arrow-up-right')}</a></p>
    </div>
    <div class="card card-dark">
      <div style="display:grid;gap:24px"><span class="label red">Geven</span>
        <h2 class="display h-md">Bouw mee aan een<br>generatie van geloof.</h2>
        <p class="body">Ashviens salaris wordt volledig betaald uit zijn eigen bedrijven. Elke gift gaat dus rechtstreeks naar boeken, Bijbelscholen en gospeltrucks.</p></div>
      <ul class="options">
        <li><a href="{LINKS['give_partner']}" target="_blank" rel="noopener">Maandelijks partner worden {icon('arrow-right')}</a></li>
        <li><a href="{LINKS['give_truck']}" target="_blank" rel="noopener">Sponsor een gospeltruck {icon('arrow-right')}</a></li>
        <li><a href="{LINKS['give_big']}" target="_blank" rel="noopener">Eenmalige gift {icon('arrow-right')}</a></li></ul>
      <p class="small-label mute anbi"><a href="{LINKS['anbi']}" target="_blank" rel="noopener">Faith Generation heeft de ANBI-status. Je gift is fiscaal aftrekbaar.</a></p>
    </div>
  </div>
</section>
{jesus_cta()}'''
    return page("Ashvien Jitan | Evangelist, spreker en schrijver",
                "Evangelist Ashvien Jitan, oprichter van Faith Generation. Bekijk preken en genezingsdiensten, bestel gratis christelijke boeken en zie waar hij spreekt.",
                "/", main, preload="/img/hero.jpg",
                schema=[{"@graph": [PERSON, {"@type": "WebSite", "@id": f"{SITE_URL}/#website", "url": f"{SITE_URL}/",
                                            "name": "Ashvien Jitan", "inLanguage": "nl-NL", "publisher": {"@id": f"{SITE_URL}/#ashvien"}}]},
                        *event_schema(events)])


TIMELINE = [
    ("14 jaar", "Tot bekering", "Ashvien is niet christelijk opgevoed. Op veertienjarige leeftijd komt hij tot bekering bij de Johan Maasbach Wereldzending in Leiden."),
    ("15 jaar", "De Levensstroom", "Na een jaar sluit hij zich aan bij de Levensstroom in Leiderdorp en bezoekt hij drie jaar lang bijna alle diensten van Jan Zijlstra. Daar wordt het verlangen geboren om te spreken en te bidden voor de zieken."),
    ("±10 jaar", "Assistent van Arno van der Knaap", "Als Arno van der Knaap, de geestelijke zoon van Jan Zijlstra, voorganger wordt, ondersteunt Ashvien hem bijna tien jaar lang in zijn bediening."),
    ("2022", "Ingezegend als evangelist", "In dezelfde periode spreekt God tegen Ashvien en geeft hem een duidelijke opdracht: “Ashvien, wek een generatie van geloof op.”"),
    ("2023", "Stichting Faith Generation", "Sindsdien gaat het snel: twintig boeken, vertaald in veertien talen en wereldwijd gratis uitgedeeld. Een driejarige fulltime Bijbelschool in India, online Bijbelscholen in verschillende talen en nieuwe bedieningen die uit Faith Generation voortkomen."),
    ("Nov 2025", "Veertig gospeltrucks", "Pastor Jaap Dieleman draagt de veertig gospeltrucks die dagelijks in India rijden over aan Ashvien. Maandelijks kiezen 200.000 tot 250.000 mensen voor de Here Jezus en worden ze direct verbonden met lokale kerken, waar ze het onderwijs van Ashvien kunnen volgen."),
]


def about():
    tl = "".join(f'<li><span class="year{" red" if y == "2022" else ""}">{y.upper()}</span><div><h3>{h}</h3><p class="body">{b}</p></div></li>'
                 for y, h, b in TIMELINE)
    main = f'''
<section class="page-head photo" style="background-image:url('/img/prediking-podium.jpg')">
  {header('/over-ashvien/')}
  <div><span class="label crumb">Home / Over Ashvien</span>
    <h1 class="display h-xl">Wek een generatie<br>van geloof op.</h1>
    <p class="sub">Dat is wat God tegen Ashvien zei. En dat is precies wat hij nu doet.</p></div>
</section>

<section class="section light">
  <div class="story">
    <div class="story-intro">
      <span class="label red">Hoe het allemaal begon</span>
      <h2 class="display" style="font-size:clamp(46px,5vw,72px)">Van bekeerling tot evangelist.</h2>
      <p class="body">Ashvien is niet christelijk opgevoed. Op veertienjarige leeftijd kwam hij tot bekering. Vanaf dat moment groeide er één verlangen: spreken over Jezus en bidden voor de zieken.</p>
      <img src="/img/gebed.jpg" alt="Ashvien bidt voor mensen tijdens een dienst" loading="lazy">
    </div>
    <ol class="timeline">{tl}</ol>
  </div>
</section>

<section class="section dark">
  <h2 class="display h-lg" style="margin:0 0 64px">Waar Ashvien<br>om bekend staat.</h2>
  <div class="known">
    <div><img src="/img/onderwijs.jpg" alt="Ashvien geeft les" loading="lazy"><h3>Simpel onderwijs</h3>
      <p class="body">God heeft Ashvien duidelijk de gave gegeven om te onderwijzen. Dingen die simpel zijn, weet hij nog simpeler uit te leggen. Dingen die moeilijk zijn, maakt hij juist makkelijk.</p></div>
    <div><img src="/img/genezingsdienst.jpg" alt="Genezingsdienst met mensen die hun handen opheffen" loading="lazy"><h3>Wonderen &amp; tekenen</h3>
      <p class="body">Ashvien vloeit in de profetische gave en in zijn diensten zijn altijd sterke wonderen en tekenen zichtbaar. Mensen worden door Gods liefde genezen van de meest heftige kwalen.</p></div>
  </div>
</section>

<section class="section light">
  <div class="blocks">
    <div><h3>Iedere leider heeft een leider nodig.</h3>
      <p class="body">Pastor Jaap Dieleman is officieel de overziener van Faith Generation en van Ashvien Jitan. Zo is niemand in het lichaam van Christus onafhankelijk. We hebben elkaar namelijk nodig.</p></div>
    <div><h3>Naast de bediening.</h3>
      <p class="body">Ashvien is naast de bediening ook eigenaar van een aantal bedrijven. In 2018 startte hij zijn eerste bedrijf; inmiddels zijn dat meerdere bedrijven die de bediening helpen financieren en zijn volledige salaris betalen.</p></div>
  </div>
</section>
{jesus_cta()}'''
    return page("Over Ashvien Jitan | Evangelist en oprichter Faith Generation",
                "Het verhaal van evangelist Ashvien Jitan: van bekering op zijn veertiende tot Faith Generation, Bijbelscholen en veertig gospeltrucks in India.",
                "/over-ashvien/", main, head_inside=True, preload="/img/prediking-podium.jpg",
                schema=[{"@type": "AboutPage", "url": f"{SITE_URL}/over-ashvien/", "mainEntity": PERSON}])


def shop(books):
    numbered = [b for b in books if b["num"]]
    filters = [("alle", "Alle boeken"), ("genezing", "Genezing"), ("gebed", "Gebed"),
               ("groei", "Geestelijke groei"), ("evangelisatie", "Evangelisatie")]
    ftabs = "".join(f'<a href="#" data-filter="{k}"{" class=active" if k == "alle" else ""}>{l}</a>' for k, l in filters)
    main = f'''
<section class="page-head dark">
  {header('/webshop/')}
  <div class="title-row"><div><span class="label crumb red">Home / Webshop</span><h1 class="display" style="font-size:clamp(64px,12.5vw,180px);line-height:.88">Boeken.</h1></div>
    <p class="body" style="max-width:440px;color:var(--body-dark)">Simpel onderwijs om te lezen, te herlezen en weg te geven. Alle boeken zijn gratis en worden verzonden via de webshop van Faith Generation.</p></div>
</section>
<div class="filters"><nav class="tabs" aria-label="Filter boeken">{ftabs}</nav><span class="small-label lang">Nederlands</span></div>
<section class="section light" style="padding-top:56px">
  <div class="books five">{book_cards(numbered, eager=5)}</div>
  {package_banner(books)}
  <p class="auto-note">{icon('refresh')} Boeken worden automatisch bijgewerkt vanuit de webshop van Faith Generation</p>
</section>'''
    return page("Gratis christelijke boeken van Ashvien Jitan | Webshop",
                f"{len(numbered)} christelijke boeken van Ashvien Jitan over geloof, gebed en genezing. Gratis te bestellen via de webshop van Faith Generation.",
                "/webshop/", main, head_inside=True,
                schema=[{"@type": "ItemList", "name": "Boeken van Ashvien Jitan", "itemListElement": [
                    {"@type": "ListItem", "position": i, "item": {"@type": "Book", "name": b["title"], "url": b["url"],
                     "author": {"@id": f"{SITE_URL}/#ashvien"}, "inLanguage": "nl", **({"image": b["cover"]} if b["cover"] else {})}}
                    for i, b in enumerate(numbered, 1)]}])


def teaching(sermons):
    chans = [("01", "Preken", "Genezingsdiensten en preken uit kerken in binnen- en buitenland.", "#preken",
              "/img/genezingsdienst.jpg"),
             ("02", "Faith Teachings", "Korte, praktische lessen om direct toe te passen in je dagelijks leven.", LINKS["teachings"], "/img/onderwijs.jpg"),
             ("03", "Podcast", "Onderwijs om onderweg te luisteren, in meerdere talen.", LINKS["podcast"], "/img/prediking-podium.jpg"),
             ("04", "Bijbelscholen", "Een fulltime Bijbelschool in India en online Bijbelscholen in verschillende talen.", LINKS["bibleschool"], "/img/gebed.jpg")]
    cards = "".join(f'''<a class="channel" href="{h}"{ext(h)} style="background-image:url('{img}')">
      <div class="top">{icon('arrow-up-right')}</div>
      <div><h3>{t}</h3><p>{d}</p></div></a>''' for n, t, d, h, img in chans)
    main = f'''
<section class="page-head dark">
  {header('/onderwijs/')}
  <span class="label crumb red">Home / Onderwijs</span><h1 class="display" style="font-size:clamp(64px,12.5vw,180px);line-height:.88">Onderwijs.</h1>
</section>
<div class="channels dark">{cards}</div>
<section class="section dark" id="preken" style="padding-top:0">
  <h2 class="display" style="font-size:clamp(40px,4.4vw,64px);margin-bottom:40px">Nieuwste preken</h2>
  {sermon_block(sermons, list_count=6)}
</section>
{jesus_cta()}'''
    return page("Preken en onderwijs van Ashvien Jitan",
                "Bekijk de nieuwste preken, genezingsdiensten en Faith Teachings van evangelist Ashvien Jitan, plus podcast en Bijbelscholen.",
                "/onderwijs/", main, head_inside=True,
                schema=[{"@type": "VideoObject", "name": sources.clean_title(s["title"]), "description": s["title"],
                         "thumbnailUrl": yt_thumb(s["id"], "hqdefault"), "uploadDate": s["date"],
                         "embedUrl": f"https://www.youtube-nocookie.com/embed/{s['id']}",
                         "url": f"https://www.youtube.com/watch?v={s['id']}"} for s in sermons[:7]])


def main():
    print("Fetching content…")
    sermons, books, events = sources.sermons(), sources.books(), sources.agenda()
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST)
    pages = {"index.html": home(sermons, books, events), "over-ashvien/index.html": about(),
             "webshop/index.html": shop(books), "onderwijs/index.html": teaching(sermons)}
    not_found = page("Pagina niet gevonden | Ashvien Jitan", "Deze pagina bestaat niet (meer).", "/404.html", f'''
<section class="page-head dark">{header('')}
  <span class="label crumb red">404</span><h1 class="display h-xl">Deze pagina<br>bestaat niet.</h1>
  <p style="margin-top:32px"><a class="btn btn-red" href="/">Naar de homepage {icon('arrow-right')}</a></p>
</section>''', head_inside=True, noindex=True)
    for path, html_out in {**pages, "404.html": not_found}.items():
        out = DIST / path
        out.parent.mkdir(parents=True, exist_ok=True)
        if BASE:
            html_out = re.sub(r'((?:href|src|srcset|poster|content)=")/(?!/)', rf"\g<1>{BASE}/", html_out)
            html_out = html_out.replace("url('/", f"url('{BASE}/")
        out.write_text(html_out)
    today = dt.date.today().isoformat()
    urls = "".join(f"<url><loc>{SITE_URL}/{p.removesuffix('index.html')}</loc><lastmod>{today}</lastmod></url>"
                   for p in pages)
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>'
                                      f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    # Plain-text summary for AI assistants and answer engines (llms.txt convention).
    (DIST / "llms.txt").write_text(
        "# Ashvien Jitan\n\n> Nederlandse evangelist, spreker en schrijver; oprichter van Stichting Faith Generation. "
        "Bekend om simpel Bijbelonderwijs en genezingsdiensten. Schreef twintig boeken die gratis worden uitgedeeld "
        "en leidt 40 gospeltrucks in India.\n\n## Pagina's\n"
        f"- [Over Ashvien]({SITE_URL}/over-ashvien/): levensverhaal, overzienerschap en bediening\n"
        f"- [Onderwijs]({SITE_URL}/onderwijs/): nieuwste preken, Faith Teachings, podcast, Bijbelscholen\n"
        f"- [Webshop]({SITE_URL}/webshop/): alle gratis boeken, te bestellen via faithgeneration.com\n"
        f"- [Agenda]({LINKS['agenda']}): diensten en events waar Ashvien spreekt\n"
        f"- [Nodig Ashvien uit]({LINKS['invite']}): spreekverzoek indienen\n")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    print(f"Built {len(pages)} pages into {DIST}")


if __name__ == "__main__":
    main()

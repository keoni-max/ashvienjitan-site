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


def yt_thumb(vid, size="hqdefault"):
    return f"https://i.ytimg.com/vi/{vid}/{size}.jpg"


# ---------- Shared chrome ----------

NAV = [("Over Ashvien", "/over-ashvien/"), ("Onderwijs", "/onderwijs/"), ("Webshop", "/webshop/"),
       ("Agenda", "/#agenda"), ("Geven", LINKS["give"])]

MOMENTS = [  # Black-and-white collage on the homepage: (file, alt text)
    ("moment-1.jpg", "Ashvien bidt voor iemand tijdens een dienst"),
    ("moment-2.jpg", "Menigte bij een evangelisatie-event in India"),
    ("moment-3.jpg", "Ashvien preekt vanaf een podium"),
    ("moment-4.jpg", "Aanbidding in een volle kerk"),
    ("moment-5.jpg", "Iemand heft de handen op in aanbidding"),
    ("moment-6.jpg", "Jongeren bidden tijdens een dienst"),
    ("moment-7.jpg", "Ashvien lacht op het podium"),
    ("moment-8.jpg", "Ashvien onderwijst een zaal vol mensen"),
    ("moment-9.jpg", "Gebed voor een bezoeker"),
    ("moment-10.jpg", "Menigte bij een gospeltruck in India"),
]


def pill(label, href, kind="ghost", ico=None, cls=""):
    """Rounded button. kind: mint | ink | ghost (light outline) | ghost-dark."""
    i = icon(ico) if ico else ""
    return f'<a class="pill pill-{kind} {cls}" href="{e(href)}"{ext(href)}>{i if ico == "play" else ""}{e(label)}{"" if ico == "play" else i}</a>'


def kicker(text):
    return f'<p class="kicker">{text}</p>'


def header(current):
    links = "".join(
        f'<a href="{href}"{ext(href)}{" aria-current=page" if href == current else ""}>{e(label)}</a>'
        for label, href in NAV)
    return f'''<header class="site-header">
  <a class="logo" href="/" aria-label="Ashvien Jitan, naar de homepage"><img src="/logo/aj-lockup-op-donker.svg" alt="Ashvien Jitan" width="308" height="54"></a>
  <nav class="nav" aria-label="Hoofdmenu">{links}</nav>
  <div class="header-actions">
    {pill("Nodig Ashvien uit", LINKS["invite"], "ghost", "arrow-up-right", "header-cta")}
    <button class="menu-toggle" type="button" aria-label="Menu openen" aria-expanded="false" aria-controls="mobile-menu">{icon('menu')}</button>
  </div>
</header>'''


def mobile_menu():
    items = [("Over Ashvien", "/over-ashvien/"),
             ("Onderwijs", [("Preken", "/onderwijs/#preken"), ("Faith Teachings", LINKS["teachings"]),
                            ("Podcast", LINKS["podcast"]), ("Bijbelscholen", LINKS["bibleschool"])]),
             ("Webshop", "/webshop/"), ("Agenda", "/#agenda"), ("Geven", LINKS["give"]), ("Contact", LINKS["contact"])]
    rows = []
    for n, (label, target) in enumerate(items, 1):
        t = f'<span class="t">{e(label)}</span>'
        if isinstance(target, list):
            sub = "".join(f'<li><a href="{h}"{ext(h)}>{e(l)} {icon("arrow-right")}</a></li>' for l, h in target)
            rows.append(f'<li><button class="mm-row" type="button" data-sub="mm-sub-{n}" aria-expanded="false">{t}'
                        f'{icon("plus", "i-plus")}{icon("minus", "i-minus")}</button>'
                        f'<ul class="mm-sub" id="mm-sub-{n}">{sub}</ul></li>')
        else:
            rows.append(f'<li><a class="mm-row" href="{target}"{ext(target)}>{t}{icon("arrow-up-right")}</a></li>')
    return f'''<div class="mobile-menu" id="mobile-menu" aria-hidden="true" role="dialog" aria-label="Menu">
  <div>
    <div class="bar"><a href="/"><img src="/logo/aj-lockup-op-donker.svg" alt="Ashvien Jitan" width="308" height="54"></a>
      <button class="menu-close" type="button" aria-label="Menu sluiten">{icon('x')}</button></div>
    <ul class="mm-list">{''.join(rows)}</ul>
  </div>
  <div class="mm-bottom">
    {pill("Nodig Ashvien uit", LINKS["invite"], "mint", "arrow-up-right")}
    {pill("Ik wil Jezus leren kennen", LINKS["jesus"], "ghost")}
    <div class="mm-social"><div class="icons">
      <a href="{LINKS['youtube']}" target="_blank" rel="noopener" aria-label="YouTube">{icon('youtube')}</a>
      <a href="{LINKS['instagram']}" target="_blank" rel="noopener" aria-label="Instagram">{icon('instagram')}</a>
      <a href="{LINKS['facebook']}" target="_blank" rel="noopener" aria-label="Facebook">{icon('facebook')}</a></div>
      <span>onderdeel van Faith Generation</span></div>
  </div>
</div>'''


def jesus_cta():
    return f'''<section class="jesus center">
  <h2>Ik wil de Here Jezus leren kennen.</h2>
  <p>De belangrijkste keuze van je leven. Je hoeft hem niet alleen te maken.</p>
  {pill("Zet de eerste stap", LINKS["jesus"], "mint", "arrow-right")}
</section>'''


def footer():
    def col(title, items):
        lis = "".join(f'<li><a href="{h}"{ext(h)}>{e(l)}</a></li>' for l, h in items)
        return f"<div><h4>{title}</h4><ul>{lis}</ul></div>"
    return f'''<footer class="site-footer">
  <div class="foot-top">
    <div class="foot-brand">
      <img src="/logo/aj-lockup-op-donker.svg" alt="Ashvien Jitan" width="308" height="54">
      <p>Nieuwe preken en boeken in je inbox via de nieuwsbrief van Faith Generation.</p>
      {pill("Schrijf je in", LINKS["newsletter"], "ghost", "arrow-up-right")}
    </div>
    <div class="foot-cols">
      {col("Navigatie", [("Over Ashvien", "/over-ashvien/"), ("Onderwijs", "/onderwijs/"), ("Webshop", "/webshop/"),
                         ("Nodig Ashvien uit", LINKS["invite"]), ("Geven", LINKS["give"]), ("Contact", LINKS["contact"])])}
      {col("Onderwijs", [("Preken", "/onderwijs/#preken"), ("Faith Teachings", LINKS["teachings"]),
                         ("Podcast", LINKS["podcast"]), ("Bijbelscholen", LINKS["bibleschool"])])}
      {col("Volg Ashvien", [("YouTube", LINKS["youtube"]), ("Instagram", LINKS["instagram"]), ("Facebook", LINKS["facebook"])])}
    </div>
  </div>
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
<meta name="theme-color" content="#0b1f1c">
<link rel="icon" href="/logo/aj-favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/logo/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
{pre}{ld}
</head>
<body>
<a class="skip-link" href="#inhoud">Naar de inhoud</a>
{'' if head_inside else header(current)}
{mobile_menu()}
<main id="inhoud">
{main}
</main>
{footer()}
<script src="/js/site.js" defer></script>
</body>
</html>
'''


# ---------- Reusable blocks ----------

def short_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {MONTHS_NL[d.month - 1].lower()}"


def sermon_block(sermons, list_count=3):
    if not sermons:
        return f'<p class="empty">Bekijk alle preken op <a href="{LINKS["youtube"]}">YouTube</a>.</p>'
    # Prefer a full service as the featured video; fall back to the newest upload.
    featured = next((s for s in sermons if sources.sermon_kind(s["title"]) in ("Genezingsdienst", "Healing Night")), sermons[0])
    rest = [s for s in sermons if s is not featured][:list_count]
    cards = "".join(f'''<a class="video-card" href="https://www.youtube.com/watch?v={s['id']}" target="_blank" rel="noopener">
      <img src="{yt_thumb(s['id'], 'mqdefault')}" alt="" loading="lazy" width="320" height="180">
      <p class="meta">{short_date(s['date'])} · {e(sources.sermon_kind(s['title']))}</p>
      <h3>{e(sources.clean_title(s['title']))}</h3></a>''' for s in rest)
    return f'''<a class="video" data-id="{featured['id']}" href="https://www.youtube.com/watch?v={featured['id']}" aria-label="Speel af: {e(sources.clean_title(featured['title']))}"
     style="background-image:url('{yt_thumb(featured['id'], 'maxresdefault')}'), url('{yt_thumb(featured['id'])}')">
    <span class="play">{icon('play')}</span></a>
  <p class="featured-caption"><span>{short_date(featured['date'])} · {e(sources.sermon_kind(featured['title']))}</span> {e(sources.clean_title(featured['title']))}</p>
  <div class="video-cards">{cards}</div>'''


def book_cards(books, eager=0):
    cards = []
    for i, b in enumerate(books):
        t = b["title"].lower()
        cats = " ".join(c for c, keys in BOOK_CATEGORIES.items() if any(k in t for k in keys))
        cover = ""
        if b["cover"]:
            src, srcset = e(b["cover"]), ""
            if b["cover"].endswith(".png"):  # WooCommerce square thumbnails exist for the 3D mock-ups
                base = b["cover"][:-4]
                srcset = (f' srcset="{e(base)}-300x300.png 300w, {e(base)}-600x600.png 600w, {src} 1080w"'
                          f' sizes="(max-width: 760px) 45vw, 22vw" onerror="this.removeAttribute(\'srcset\')"')
            cover = f'<img src="{src}"{srcset} alt="Omslag: {e(b["title"])}" loading="{"eager" if i < eager else "lazy"}" width="300" height="300">'
        num = f'<span class="num">Boek {b["num"]}</span>' if b["num"] else ""
        cards.append(f'''<a class="book" href="{e(b['url'])}" target="_blank" rel="noopener" data-cat="{cats}">
      <div class="cover">{cover}</div>
      {num}<h3>{e(b['title'])}</h3>
      <span class="order">{e(b['price'])} · bestellen {icon('arrow-right')}</span></a>''')
    return "".join(cards)


def package_banner(books):
    pkg = next((b for b in books if "pakket" in b["title"].lower()), None)
    href = pkg["url"] if pkg else LINKS["shop"]
    return f'''<div class="package"><div><h3>Alle twintig boeken in één pakket</h3>
    <p>Boek 1 tot en met 20, via de webshop van Faith Generation.</p></div>
    {pill("Naar het boekpakket", href, "mint", "arrow-up-right")}</div>'''


def agenda_block(events, limit=None):
    if not events:
        return f'<p class="empty">Er staan op dit moment geen diensten gepland. Bekijk de <a href="{LINKS["agenda"]}">agenda van Faith Generation</a>.</p>'
    rows = []
    for ev in events[:limit]:
        times = ", ".join(t for t, _ in ev["sessions"])
        label = next((l for _, l in ev["sessions"] if l), "")
        city = ev["place"].split(",")[-1].strip() if ev["place"] else ""
        href = ev["ticket"] or LINKS["agenda"]
        meta = " · ".join(x for x in (city, times, label) if x)
        rows.append(f'''<li><a href="{e(href)}" target="_blank" rel="noopener">
      <span class="ev-date"><b>{e(ev['day'])}</b>{e(ev['month'].lower())}</span>
      <span class="ev-info"><b>{e(ev['title'])}</b><span>{e(meta)}</span></span>
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


def collage():
    cols = []
    for i in range(5):
        top, bottom = MOMENTS[i], MOMENTS[i + 5]
        cols.append(f'<div class="col{" offset" if i % 2 else ""}">'
                    + "".join(f'<img src="/img/{f}" alt="{e(a)}" loading="lazy" width="900" height="900">' for f, a in (top, bottom))
                    + "</div>")
    return f'<div class="collage">{"".join(cols)}</div>'


def home(sermons, books, events):
    slides = "".join(
        (f'<video src="{s["video"]}" poster="{s["img"]}" muted playsinline loop preload="none"></video>' if s.get("video")
         else f'<img src="{s["img"]}" alt="" {"fetchpriority=high" if i == 0 else "loading=lazy"}>')
        for i, s in enumerate(HERO_SLIDES))
    shop_books = [b for b in books if b["num"] in (1, 6, 13)] or [b for b in books if b["num"]][:3]
    main = f'''
<section class="hero">
  <div class="hero-media" aria-hidden="true">{slides}</div>
  <div class="hero-content">
    {kicker("Evangelist · Faith Generation")}
    <h1>Reviving a generation of faith</h1>
    <p class="hero-sub">Simpel Bijbelonderwijs, gratis boeken en diensten waarin mensen genezing ervaren.</p>
    <div class="buttons">
      {pill("Bekijk de laatste preek", "/onderwijs/#preken", "mint", "play")}
      {pill("Ik wil Jezus leren kennen", LINKS["jesus"], "ghost")}
    </div>
  </div>
</section>

<section class="section center intro">
  {kicker("Over Ashvien")}
  <h2>Een generatie van geloof opwekken. Dat is zijn opdracht.</h2>
  <p class="lead">Ashvien Jitan kwam op zijn veertiende tot geloof. Vandaag legt hij de Bijbel zo simpel uit dat je er morgen mee aan de slag kunt, bidt hij voor zieken en deelt hij met veertig gospeltrucks dagelijks het evangelie in India.</p>
  {pill("Lees zijn verhaal", "/over-ashvien/", "ghost-dark", "arrow-right")}
  <img class="wide-photo bw" src="/img/prediking-podium.jpg" alt="Ashvien Jitan preekt op een podium" loading="lazy" width="1920" height="1280">
</section>

<section class="section center moments">
  <h2 class="h-md">Mensen die Jezus leren kennen, genezen en groeien.</h2>
  {collage()}
</section>

<section class="section dark center" id="onderwijs">
  {kicker("Preken &amp; onderwijs")}
  <h2>Elke week nieuwe preken.</h2>
  <div class="sermons">{sermon_block(sermons)}</div>
  {pill("Alle preken op YouTube", LINKS["youtube"], "ghost", "arrow-up-right")}
</section>

<section class="section books-teaser">
  <div class="books-text">
    {kicker("Boeken")}
    <h2 class="h-md">20 boeken. Gratis voor iedereen.</h2>
    <p>Over geloof, gebed en genezing. Vertaald in veertien talen en gratis te bestellen via de webshop van Faith Generation.</p>
    {pill("Bekijk alle boeken", "/webshop/", "ink", "arrow-right")}
  </div>
  <div class="books three">{book_cards(shop_books)}</div>
</section>

<section class="trucks-wrap">
  <div class="trucks center" style="background-image:url('/img/gospeltruck-india.jpg')">
    {kicker("Gospeltrucks India")}
    <h2>40 trucks. Elke dag het evangelie.</h2>
    <p>Elke maand kiezen 200.000 tot 250.000 mensen voor de Here Jezus. Ze worden direct verbonden met een lokale kerk.</p>
    {pill("Lees getuigenissen", LINKS["testimonies"], "ghost", "arrow-up-right")}
  </div>
</section>

<section class="section center" id="agenda">
  {kicker("Agenda")}
  <h2 class="h-md">Hier kun je Ashvien zien.</h2>
  {agenda_block(events, limit=6)}
  {pill("Volledige agenda", LINKS["agenda"], "ghost-dark", "arrow-up-right")}
</section>

<section class="cards-wrap">
  <div class="card card-photo" style="background-image:url('/img/genezing.jpg')">
    {kicker("Nodig Ashvien uit")}
    <h2>Een genezingsdienst, seminar of conferentie in jouw kerk?</h2>
    <p>Ashvien spreekt in kerken, op conferenties en revival-weekenden. Hij staat onder overzienerschap van pastor Jaap Dieleman.</p>
    <div>{pill("Spreekverzoek indienen", LINKS["invite"], "mint", "arrow-up-right")}</div>
  </div>
  <div class="card card-green">
    <div class="card-top">
      {kicker("Geven")}
      <h2>Bouw mee aan een generatie van geloof.</h2>
      <p>Ashviens salaris komt uit zijn eigen bedrijven. Jouw gift gaat naar boeken, Bijbelscholen en gospeltrucks.</p>
    </div>
    <ul class="options">
      <li><a href="{LINKS['give_partner']}" target="_blank" rel="noopener">Maandelijks partner worden {icon('arrow-right')}</a></li>
      <li><a href="{LINKS['give_truck']}" target="_blank" rel="noopener">Sponsor een gospeltruck {icon('arrow-right')}</a></li>
      <li><a href="{LINKS['give_big']}" target="_blank" rel="noopener">Eenmalige gift {icon('arrow-right')}</a></li>
    </ul>
    <p class="anbi"><a href="{LINKS['anbi']}" target="_blank" rel="noopener">Faith Generation heeft de ANBI-status. Je gift is fiscaal aftrekbaar.</a></p>
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


def page_head(current, title, sub="", photo=None):
    style = f' style="background-image:url(\'{photo}\')"' if photo else ""
    return f'''<section class="page-head{' photo' if photo else ''}"{style}>
  {header(current)}
  <div class="page-title">
    <h1>{title}</h1>
    {f'<p class="sub">{sub}</p>' if sub else ''}
  </div>
</section>'''


def about():
    tl = "".join(f'<li><span class="year">{y}</span><div><h3>{h}</h3><p>{b}</p></div></li>' for y, h, b in TIMELINE)
    main = f'''
{page_head('/over-ashvien/', 'Wek een generatie van geloof op.', 'Dat is wat God tegen Ashvien zei. En dat is precies wat hij nu doet.', '/img/prediking-podium.jpg')}

<section class="section story">
  <div class="story-intro">
    {kicker("Hoe het allemaal begon")}
    <h2 class="h-md">Van bekeerling tot evangelist.</h2>
    <p>Ashvien is niet christelijk opgevoed. Op veertienjarige leeftijd kwam hij tot bekering. Vanaf dat moment groeide er één verlangen: spreken over Jezus en bidden voor de zieken.</p>
    <img class="bw" src="/img/gebed.jpg" alt="Ashvien bidt voor mensen tijdens een dienst" loading="lazy" width="1280" height="1920">
  </div>
  <ol class="timeline">{tl}</ol>
</section>

<section class="section dark center">
  <h2>Waar Ashvien om bekend staat.</h2>
  <div class="known">
    <div><img class="bw" src="/img/onderwijs.jpg" alt="Ashvien geeft les" loading="lazy" width="1920" height="1063"><h3>Simpel onderwijs</h3>
      <p>God heeft Ashvien de gave gegeven om te onderwijzen. Dingen die simpel zijn, legt hij nog simpeler uit. Dingen die moeilijk zijn, maakt hij juist makkelijk.</p></div>
    <div><img class="bw" src="/img/genezingsdienst.jpg" alt="Genezingsdienst met mensen die hun handen opheffen" loading="lazy" width="1280" height="1920"><h3>Wonderen en tekenen</h3>
      <p>Ashvien vloeit in de profetische gave en in zijn diensten zijn sterke wonderen en tekenen zichtbaar. Mensen worden door Gods liefde genezen van de meest heftige kwalen.</p></div>
  </div>
</section>

<section class="section blocks">
  <div><h3>Iedere leider heeft een leider nodig.</h3>
    <p>Pastor Jaap Dieleman is officieel de overziener van Faith Generation en van Ashvien Jitan. Zo is niemand in het lichaam van Christus onafhankelijk. We hebben elkaar namelijk nodig.</p></div>
  <div><h3>Naast de bediening.</h3>
    <p>Ashvien is ook eigenaar van een aantal bedrijven. In 2018 startte hij zijn eerste bedrijf; inmiddels zijn dat meerdere bedrijven die de bediening helpen financieren en zijn volledige salaris betalen.</p></div>
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
{page_head('/webshop/', 'Boeken.', 'Simpel onderwijs om te lezen, te herlezen en weg te geven. Alle boeken zijn gratis en worden verzonden via de webshop van Faith Generation.')}
<div class="filters"><nav class="chips" aria-label="Filter boeken">{ftabs}</nav></div>
<section class="section shop">
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
    chans = [("Preken", "Genezingsdiensten en preken uit kerken in binnen- en buitenland.", "#preken", "/img/genezingsdienst.jpg"),
             ("Faith Teachings", "Korte, praktische lessen om direct toe te passen in je dagelijks leven.", LINKS["teachings"], "/img/onderwijs.jpg"),
             ("Podcast", "Onderwijs om onderweg te luisteren, in meerdere talen.", LINKS["podcast"], "/img/prediking-podium.jpg"),
             ("Bijbelscholen", "Een fulltime Bijbelschool in India en online Bijbelscholen in verschillende talen.", LINKS["bibleschool"], "/img/moment-8.jpg")]
    cards = "".join(f'''<a class="channel" href="{h}"{ext(h)} style="background-image:url('{img}')">
      <span class="channel-go">{icon('arrow-up-right')}</span>
      <div><h3>{t}</h3><p>{d}</p></div></a>''' for t, d, h, img in chans)
    main = f'''
{page_head('/onderwijs/', 'Onderwijs.', 'Preken, korte lessen, een podcast en Bijbelscholen. Alles om het Woord van God te begrijpen en toe te passen.')}
<section class="section dark channels-wrap"><div class="channels">{cards}</div></section>
<section class="section dark center" id="preken">
  <h2>Nieuwste preken</h2>
  <div class="sermons">{sermon_block(sermons, list_count=6)}</div>
  {pill("Alle preken op YouTube", LINKS["youtube"], "ghost", "arrow-up-right")}
  <p class="auto-note">{icon('refresh')} Wordt automatisch bijgewerkt vanuit het YouTube-kanaal van Faith Generation</p>
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
{page_head('', 'Deze pagina bestaat niet.', 'Misschien is hij verhuisd. Begin opnieuw op de homepage.')}
<section class="section center">{pill("Naar de homepage", "/", "ink", "arrow-right")}</section>''', head_inside=True, noindex=True)
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

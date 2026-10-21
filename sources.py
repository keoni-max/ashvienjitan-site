"""Fetches live content from YouTube and faithgeneration.com.

Every fetcher falls back to the last good copy in data/ when the source is
unreachable, so a build never produces an empty page.
"""
import datetime as dt
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DATA = Path(__file__).parent / "data"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"

YOUTUBE_CHANNEL = "UCHLfXcDbVr49nuHQLh_TMYA"
SHOP_URL = "https://faithgeneration.com/shop/"
AGENDA_URL = "https://faithgeneration.com/agenda/"

MONTHS = {"jan": 1, "feb": 2, "mrt": 3, "maa": 3, "apr": 4, "mei": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "nl-NL,nl;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def cached(name, loader, minimum=1):
    """Run loader; on failure or a suspiciously small result, use the cached copy."""
    path = DATA / f"{name}.json"
    try:
        items = loader()
        if len(items) < minimum:
            raise ValueError(f"only {len(items)} items")
        path.write_text(json.dumps(items, indent=1, ensure_ascii=False))
        print(f"  {name}: {len(items)} live")
        return items
    except Exception as e:  # network down, markup changed, Cloudflare block …
        items = json.loads(path.read_text()) if path.exists() else []
        print(f"  {name}: using cache ({len(items)}) — {e}")
        return items


# ---------- Preken (YouTube) ----------

def _sermons():
    xml = fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL}")
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    out = []
    for e in ET.fromstring(xml).findall("a:entry", ns):
        vid = e.find("yt:videoId", ns).text
        out.append({
            "id": vid,
            "title": e.find("a:title", ns).text,
            "date": e.find("a:published", ns).text[:10],
        })
    return out


def sermons():
    return cached("sermons", _sermons, minimum=3)


def clean_title(title):
    """Drop suffixes that repeat the speaker or the series label shown next to it."""
    parts = [p.strip() for p in title.split("|")]
    keep = [p for p in parts[1:] if not re.search(r"ashvien|faith teaching|equip teaching", p, re.I)]
    return " | ".join([parts[0], *keep])


def sermon_kind(title):
    t = title.lower()
    for key, label in (("faith teaching", "Faith Teaching"), ("equip", "Equip Teaching"),
                       ("genezingsdienst", "Genezingsdienst"), ("healing", "Healing Night"),
                       ("podcast", "Podcast")):
        if key in t:
            return label
    return "Preek"


# ---------- Boeken (WooCommerce webshop) ----------

def _books():
    out, seen = [], set()
    for page in (SHOP_URL, SHOP_URL + "page/2/", SHOP_URL + "page/3/"):
        try:
            s = fetch(page)
        except Exception:
            break
        for m in re.finditer(r'product_card-title[^>]*><a href="([^"]+)">(.*?)</a>', s):
            url, title = m.group(1), html.unescape(m.group(2)).strip()
            if url in seen:
                continue
            seen.add(url)
            tail = s[m.end():m.end() + 6000]
            price = re.search(r'class="price">(.*?)</p>', tail, re.S)
            price = " ".join(html.unescape(re.sub("<[^>]+>", " ", price.group(1))).split()) if price else ""
            cover = re.search(r'&quot;url&quot;:&quot;(https:[^&]+?\.(?:png|jpe?g|webp))', tail)
            num = re.match(r"Boek\s+(\d+)\s*\|\s*(.*)", title)
            out.append({
                "num": int(num.group(1)) if num else None,
                "title": num.group(2) if num else title,
                "url": url,
                "price": price or "Gratis",
                "cover": cover.group(1).replace("\\/", "/") if cover else "",
            })
    out.sort(key=lambda b: (b["num"] is None, b["num"] or 0))
    return out


def books():
    items = cached("books", _books, minimum=5)
    # The cache from the first scrape uses the old field names; normalise.
    norm = []
    for b in items:
        if "num" not in b:
            m = re.match(r"Boek\s+(\d+)\s*\|\s*(.*)", b["title"])
            b = {"num": int(m.group(1)) if m else None, "title": m.group(2) if m else b["title"],
                 "url": b["url"], "price": b.get("price") or "Gratis", "cover": b.get("cover", "")}
        norm.append(b)
    norm.sort(key=lambda b: (b["num"] is None, b["num"] or 0))
    return norm


# ---------- Agenda (faithgeneration.com/agenda) ----------

def _session_date(text, today):
    m = re.search(r"(\d{1,2})\s+([a-z]{3})", text.lower())
    if not m or m.group(2) not in MONTHS:
        return None
    month, day = MONTHS[m.group(2)], int(m.group(1))
    year = today.year + (1 if month < today.month - 2 else 0)
    return dt.date(year, month, day)


def _agenda():
    s = fetch(AGENDA_URL)
    today = dt.date.today()
    out = []
    for block in s.split('class="brxe-xasfyc')[1:]:
        title = re.search(r"<h3[^>]*>(.*?)</h3>", block, re.S)
        if not title:
            continue
        datebox = re.search(r"<strong>(.*?)</strong><br>\s*([a-z]+)", block)
        place = re.search(r'brxe-dqekii[^>]*>(.*?)</div>', block, re.S)
        sessions = [(" ".join(html.unescape(t).split()), html.unescape(l).strip())
                    for t, l in re.findall(r'uppercase w-800">(.*?)</div><div class="brxe-vivjtm[^>]*>(.*?)</div>', block)]
        ticket = re.search(r'<a class="[^"]*bricks-button" href="([^"]+)"', block)
        dates = [d for d in (_session_date(t, today) for t, _ in sessions) if d]
        if dates and max(dates) < today:
            continue
        out.append({
            "title": html.unescape(re.sub("<[^>]+>", "", title.group(1))).strip(),
            "day": html.unescape(datebox.group(1)).replace("-", "–") if datebox else "",
            "month": datebox.group(2).upper() if datebox else "",
            "place": html.unescape(place.group(1)).strip() if place else "",
            "sessions": sessions,
            "ticket": html.unescape(ticket.group(1)) if ticket else "",
            "first": min(dates).isoformat() if dates else "",
            "last": max(dates).isoformat() if dates else "",
        })
    out.sort(key=lambda e: e["first"] or "9999")
    return out


def agenda():
    items = cached("agenda", _agenda, minimum=0)
    today = dt.date.today().isoformat()
    # Drop cached events that have passed since the last successful fetch.
    return [e for e in items if not e.get("last") or e["last"] >= today]

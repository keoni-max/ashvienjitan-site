# ashvienjitan.nl

Statische website voor Ashvien Jitan. Geen CMS, geen wekelijks onderhoud: bij elke build
worden de nieuwste preken, boeken en agenda automatisch opgehaald.

| Inhoud | Bron | Waar het staat |
|---|---|---|
| Preken | YouTube-kanaal Faith Generation (RSS) | Home, Onderwijs |
| Boeken | Webshop faithgeneration.com/shop | Home, Webshop — bestellen gaat via de FG-webshop |
| Agenda | faithgeneration.com/agenda | Home |
| Nodig uit, Geven, Contact, Jezus leren kennen | Links naar faithgeneration.com | overal |

Als een bron tijdelijk onbereikbaar is, gebruikt de build de laatst opgehaalde versie uit `data/`.

## Bouwen

```bash
python3 build.py
```

Alleen Python 3 nodig, geen extra pakketten. Resultaat staat in `dist/`.

Lokaal bekijken:

```bash
cd dist && python3 -m http.server 8087
```

## Publiceren

`.github/workflows/build.yml` bouwt de site elke ochtend opnieuw en publiceert naar
GitHub Pages. Elke andere statische host werkt ook (Netlify, Cloudflare Pages, Vercel):
build-commando `python3 build.py`, publish-map `dist`, plus een dagelijkse rebuild.

## Aanpassen

- **Teksten**: in `build.py` (functies `home`, `about`, `shop`, `teaching`).
- **Homepagevideo's**: zet een mp4 in `static/video/` en voeg `"video": "/video/naam.mp4"` toe
  aan de juiste regel in `HERO_SLIDES` in `build.py`.
- **Links** naar Faith Generation: `LINKS` bovenaan `build.py`.
- **Stijl**: `static/css/style.css`. Logo-bestanden staan in `logo/`.

(() => {
  const body = document.body;
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Mobile menu
  const menu = document.querySelector(".mobile-menu");
  const openMenu = (open) => {
    menu.classList.toggle("open", open);
    body.classList.toggle("menu-open", open);
    menu.setAttribute("aria-hidden", String(!open));
    document.querySelectorAll(".menu-toggle").forEach((b) => b.setAttribute("aria-expanded", String(open)));
    if (open) menu.querySelector(".menu-close").focus();
  };
  document.querySelectorAll(".menu-toggle").forEach((b) => b.addEventListener("click", () => openMenu(true)));
  menu?.querySelector(".menu-close").addEventListener("click", () => openMenu(false));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && menu?.classList.contains("open")) openMenu(false); });
  menu?.querySelectorAll("[data-sub]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sub = document.getElementById(btn.dataset.sub);
      const open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", String(open));
      sub.classList.toggle("open", open);
    });
  });

  // Header: hide while scrolling down, come back (solid white) while scrolling up
  const header = document.querySelector("[data-header]");
  if (header) {
    let last = scrollY, ticking = false;
    const update = () => {
      const y = scrollY, past = y > 120;
      header.classList.toggle("solid", past && y < last);
      header.classList.toggle("hidden", past && y > last && !body.classList.contains("menu-open"));
      if (!past) header.classList.remove("solid", "hidden");
      last = y; ticking = false;
    };
    addEventListener("scroll", () => { if (!ticking) { requestAnimationFrame(update); ticking = true; } }, { passive: true });
  }

  // Hero: crossfade between slides (photo or video)
  const hero = document.querySelector(".hero");
  if (hero) {
    const slides = [...hero.querySelectorAll(".hero-media > *")];
    let i = 0;
    const show = (n) => {
      i = (n + slides.length) % slides.length;
      slides.forEach((s, k) => {
        s.style.opacity = k === i ? "1" : "0";
        if (s.tagName === "VIDEO") k === i ? s.play().catch(() => {}) : s.pause();
      });
      setTimeout(() => show(i + 1), 7000);
    };
    if (slides.length > 1 && !calm) setTimeout(() => show(1), 7000);
  }

  // Count numbers up from zero, Dutch thousands separator
  const fmt = (n) => Math.round(n).toLocaleString("nl-NL");
  const countUp = (el) => {
    const target = Number(el.dataset.count), suffix = el.dataset.suffix || "";
    if (calm) { el.textContent = fmt(target) + suffix; return; }
    const start = performance.now(), dur = 1400;
    const step = (t) => {
      const p = Math.min(1, (t - start) / dur), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(target * eased) + (p === 1 ? suffix : "");
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  // Reveal on scroll (headings, text, photos, rows) and start counters when visible
  const reveal = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      en.target.classList.add("in");
      en.target.querySelectorAll?.("[data-count]").forEach(countUp);
      if (en.target.matches?.("[data-count]")) countUp(en.target);
      reveal.unobserve(en.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
  document.querySelectorAll("[data-reveal], .trucks, .proof").forEach((el) => reveal.observe(el));

  // Gentle parallax on the collage rows and the gospeltruck photo
  const layers = [...document.querySelectorAll("[data-parallax]")];
  if (layers.length && !calm) {
    let ticking = false;
    const move = () => {
      const vh = innerHeight;
      layers.forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.bottom < 0 || r.top > vh) return;
        const progress = (r.top + r.height / 2 - vh / 2) / vh; // -1 … 1 around the centre
        el.style.transform = `translate3d(0, ${(progress * Number(el.dataset.parallax)).toFixed(1)}px, 0)`;
      });
      ticking = false;
    };
    addEventListener("scroll", () => { if (!ticking) { requestAnimationFrame(move); ticking = true; } }, { passive: true });
    move();
  }

  // Sermon carousel: arrow buttons scroll one card; arrows dim at the ends
  document.querySelectorAll("[data-carousel]").forEach((track) => {
    const section = track.closest(".sermons");
    const prev = section?.querySelector("[data-carousel-prev]"), next = section?.querySelector("[data-carousel-next]");
    if (!prev || !next) return;
    const stepSize = () => (track.firstElementChild?.getBoundingClientRect().width || 300) + 24;
    const sync = () => {
      prev.disabled = track.scrollLeft < 4;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
      prev.classList.toggle("round-mint", !prev.disabled && next.disabled);
      next.classList.toggle("round-mint", !next.disabled);
    };
    prev.addEventListener("click", () => track.scrollBy({ left: -stepSize(), behavior: calm ? "auto" : "smooth" }));
    next.addEventListener("click", () => track.scrollBy({ left: stepSize(), behavior: calm ? "auto" : "smooth" }));
    track.addEventListener("scroll", () => requestAnimationFrame(sync), { passive: true });
    sync();
  });

  // "Meer onderwijs": one item open at a time, the photo follows the open item
  document.querySelectorAll("[data-tracks]").forEach((group) => {
    const img = group.closest("section").querySelector("[data-tracks-img]");
    const items = [...group.querySelectorAll("details")];
    items.forEach((d) => d.addEventListener("toggle", () => {
      if (!d.open) return;
      items.forEach((o) => { if (o !== d) o.open = false; });
      if (img && img.getAttribute("src") !== d.dataset.img) {
        img.style.opacity = "0";
        setTimeout(() => { img.src = d.dataset.img; img.onload = () => { img.style.opacity = "1"; }; }, calm ? 0 : 220);
      }
    }));
  });

  // Click-to-play YouTube (no YouTube scripts until the visitor asks for it)
  document.querySelectorAll("a.video[data-id]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      const f = document.createElement("iframe");
      f.src = `https://www.youtube-nocookie.com/embed/${a.dataset.id}?autoplay=1&rel=0`;
      f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      f.allowFullscreen = true;
      f.title = a.getAttribute("aria-label") || "YouTube video";
      a.replaceChildren(f);
    });
  });

  // Webshop filter (client-side, by category keyword)
  const filters = document.querySelectorAll("[data-filter]");
  filters.forEach((f) => f.addEventListener("click", (e) => {
    e.preventDefault();
    filters.forEach((x) => x.classList.toggle("active", x === f));
    const cat = f.dataset.filter;
    document.querySelectorAll(".book[data-cat]").forEach((b) => {
      b.hidden = cat !== "alle" && !b.dataset.cat.split(" ").includes(cat);
    });
  }));
})();

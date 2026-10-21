(() => {
  const body = document.body;

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

  // Hero reel: crossfade between slides (photo or video), clickable index
  const hero = document.querySelector(".hero");
  if (hero) {
    const slides = [...hero.querySelectorAll(".hero-media > *")];
    const dots = [...hero.querySelectorAll(".reel button")];
    let i = 0, timer;
    const show = (n) => {
      i = (n + slides.length) % slides.length;
      slides.forEach((s, k) => {
        s.style.opacity = k === i ? "1" : "0";
        if (s.tagName === "VIDEO") k === i ? s.play().catch(() => {}) : s.pause();
      });
      dots.forEach((d, k) => d.classList.toggle("active", k === i));
      clearTimeout(timer);
      timer = setTimeout(() => show(i + 1), 6000);
    };
    dots.forEach((d, k) => d.addEventListener("click", () => show(k)));
    if (slides.length > 1 && !matchMedia("(prefers-reduced-motion: reduce)").matches) show(0);
  }

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

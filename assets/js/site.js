/* Shared page chrome: sidebar, back-to-top button, project grids.
   Content lives in projects.js — you shouldn't need to edit this file. */
(function () {
  const root = document.body.dataset.root || "";       // "" for top-level pages, "../" inside /projects
  const page = document.body.dataset.page;              // home | more-date | more-effort | about | project
  const slug = document.body.dataset.slug || "";
  const C = window.CONTACT || {};

  const ICONS = {
    up: '<svg viewBox="0 0 37 63" aria-hidden="true"><path d="M18.5 61V3M2 19 18.5 3 35 19" fill="none" stroke="#000" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  };

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const url = (p) => (!p || /^(https?:|mailto:|#)/.test(p) ? p : root + p);
  const cur = (cond) => (cond ? ' class="is-current" aria-current="page"' : "");

  /* ---------- Sidebar ---------- */
  const aside = document.getElementById("sidebar");
  if (aside) {
    const name = `<a class="name" href="${url("index.html")}">Joshua<br>Rivera<br>Camacho</a>`;
    const socials = `<div class="socials">
        <a href="${esc(C.linkedin)}" target="_blank" rel="noopener" aria-label="LinkedIn"><img src="${url("assets/img/icons/linkedin.png")}" alt=""></a>
        <a href="mailto:${esc(C.email)}" aria-label="Email"><img src="${url("assets/img/icons/mail.png")}" alt=""></a>
      </div>`;

    if (page === "project") {
      // Section index is built from the <section data-nav="..."> blocks on the page
      const sections = [...document.querySelectorAll("main section[id]")];
      const index = sections
        .map((s) => `<a href="#${s.id}">${esc(s.dataset.nav || s.querySelector("h2")?.textContent || s.id)}</a>`)
        .join("");
      aside.innerHTML = `${name}
        <nav class="section-index" aria-label="On this page">${index}</nav>
        <div class="return">Return to...
          <div class="return__links">
            <a href="${url("index.html")}">Selected Work</a>
            <a href="${url("more-projects-by-date.html")}">More Projects</a>
            <a href="${url("about.html")}">About Me</a>
          </div>
        </div>`;

      // Highlight the section currently on screen
      const links = [...aside.querySelectorAll(".section-index a")];
      // The active section is the last one whose heading has passed 20% of the way down the window.
      // At the very bottom of the page the last section wins, so short final sections
      // (Room for Improvement, Reflection) still get highlighted.
      const setActive = (id) => links.forEach((a) => a.classList.toggle("is-active", a.getAttribute("href") === "#" + id));
      let clickedId = null;
      const spy = () => {
        if (clickedId) return setActive(clickedId);
        const line = Math.max(window.innerHeight * 0.2, 90);
        let current = sections[0];
        for (const s of sections) if (s.getBoundingClientRect().top <= line) current = s;
        const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
        if (atBottom) current = sections[sections.length - 1];
        if (current) setActive(current.id);
      };
      // Clicking a link highlights it straight away, even if that section can't scroll to the top
      links.forEach((a) => a.addEventListener("click", () => {
        clickedId = a.getAttribute("href").slice(1);
        setActive(clickedId);
      }));
      // ...and stays highlighted until the reader scrolls on their own
      const release = () => { if (clickedId) { clickedId = null; spy(); } };
      window.addEventListener("wheel", release, { passive: true });
      window.addEventListener("touchmove", release, { passive: true });
      window.addEventListener("keydown", (e) => { if (/Arrow|Page|Home|End|Space/.test(e.code)) release(); });
      document.addEventListener("mousedown", (e) => { if (!e.target.closest(".section-index")) release(); });
      window.addEventListener("scroll", spy, { passive: true });
      window.addEventListener("resize", spy);
      spy();
    } else {
      const list = (window.SELECTED_WORK || [])
        .map((p) => `<li><a href="${url("projects/" + p.slug + ".html")}"${p.slug === slug ? ' class="is-current"' : ""}>${esc(p.navTitle || p.title).replace(/\n/g, "<br>")}</a></li>`)
        .join("");
      const onMore = page === "more-date" || page === "more-effort";
      aside.innerHTML = `${name}
        <nav class="nav" aria-label="Main">
          <a href="${url("index.html")}" class="nav__link${page === "home" ? " is-current" : ""}">Selected Work</a>
          <ul class="project-list">${list}</ul>
          <a href="${url("more-projects-by-date.html")}" class="nav__link${onMore ? " is-current" : ""}">More Projects</a>
          <a href="${url("about.html")}" class="nav__link${page === "about" ? " is-current" : ""}">About Me</a>
        </nav>
        ${socials}`;
    }
  }

  /* ---------- About page buttons ---------- */
  const aboutLinks = document.getElementById("about-links");
  if (aboutLinks) {
    aboutLinks.innerHTML = `
      <a href="${esc(C.linkedin)}" target="_blank" rel="noopener" aria-label="LinkedIn"><img src="${url("assets/img/icons/linkedin.png")}" alt=""></a>
      <a href="${url(C.resume)}" target="_blank" rel="noopener">Resume</a>
      <a href="mailto:${esc(C.email)}" aria-label="Email"><img class="icon--mail" src="${url("assets/img/icons/mail.png")}" alt=""></a>`;
  }

  /* ---------- Project hero: info panel matches the photo's height ----------
     The panel is set to the photo's height, then its text size is the largest
     (up to the design size) that fits without overflowing. */
  const hero = document.querySelector(".project__hero");
  if (hero) {
    const photo = hero.querySelector(".media");
    const info = hero.querySelector(".project__info");
    const fit = () => {
      if (!photo || !info) return;
      info.style.height = "";
      info.style.fontSize = "";
      if (window.matchMedia("(max-width: 820px)").matches) return; // phones stack them
      const H = photo.getBoundingClientRect().height;
      info.style.height = H + "px";
      const base = parseFloat(getComputedStyle(info).fontSize); // design size
      let lo = base * 0.4, hi = base;
      info.style.fontSize = hi + "px";
      if (info.scrollHeight <= H + 1) return;
      for (let i = 0; i < 14; i++) {
        const mid = (lo + hi) / 2;
        info.style.fontSize = mid + "px";
        if (info.scrollHeight <= H + 1) lo = mid; else hi = mid;
      }
      info.style.fontSize = lo + "px";
    };
    fit();
    window.addEventListener("resize", fit);
    if (document.fonts) document.fonts.ready.then(fit);
    const img = photo && photo.querySelector("img");
    if (img && !img.complete) img.addEventListener("load", fit);
  }

  /* ---------- Back to top ---------- */
  const btn = document.createElement("button");
  btn.className = "to-top";
  btn.setAttribute("aria-label", "Back to top");
  btn.innerHTML = ICONS.up;
  btn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  document.body.appendChild(btn);
  const onScroll = () => btn.classList.toggle("is-visible", window.scrollY > window.innerHeight * 0.5);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Shared card markup ---------- */
  const cardInner = (p) => `
    ${p.image ? `<img src="${esc(url(p.image))}" alt="" loading="lazy">` : ""}
    <div class="card__overlay">
      <h2 class="card__title">${esc(p.title)}</h2>
      ${p.blurb ? `<p class="card__blurb">${esc(p.blurb)}</p>` : ""}
    </div>
    ${p.meta ? `<p class="card__meta">${esc(p.meta)}</p>` : ""}`;

  /* ---------- Homepage: Selected Work grid ---------- */
  const work = document.getElementById("work-grid");
  if (work) {
    work.innerHTML = (window.SELECTED_WORK || [])
      .map((p) => `<a class="card media${p.image ? " has-image" : ""}" href="${url("projects/" + p.slug + ".html")}">${cardInner(p)}</a>`)
      .join("");
  }

  /* ---------- More Projects grid (sorted by date or effort) ---------- */
  const more = document.getElementById("more-grid");
  if (more) {
    const items = [...(window.MORE_PROJECTS || [])];
    if (more.dataset.sort === "effort") items.sort((a, b) => (b.effort || 0) - (a.effort || 0));
    else items.sort((a, b) => String(b.date).localeCompare(String(a.date)));

    const fmtDate = (d) => {
      const [y, m] = String(d || "").split("-");
      if (!y) return "";
      return m ? new Date(+y, +m - 1).toLocaleString("en-US", { month: "short", year: "numeric" }) : y;
    };

    more.innerHTML = items
      .map((p) => {
        const meta = more.dataset.sort === "effort" ? "" : (p.dateLabel || fmtDate(p.date));
        const box = `<div class="media">${cardInner({ ...p, meta: p.meta ?? meta })}</div>`;
        const tag = p.link ? "a" : "div";
        const href = p.link ? ` href="${esc(url(p.link))}"` : "";
        return `<${tag} class="more-card${p.image ? " has-image" : ""}"${href}>${box}
          ${p.caption ? `<p class="more-card__caption">${esc(p.caption)}</p>` : ""}</${tag}>`;
      })
      .join("");
  }
})();

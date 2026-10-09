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
      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) links.forEach((a) => a.classList.toggle("is-active", a.getAttribute("href") === "#" + e.target.id));
        });
      }, { rootMargin: "-40% 0px -55% 0px" });
      sections.forEach((s) => io.observe(s));
    } else {
      const list = (window.SELECTED_WORK || [])
        .map((p) => `<li><a href="${url("projects/" + p.slug + ".html")}"${p.slug === slug ? ' class="is-current"' : ""}>${esc(p.title)}</a></li>`)
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
        const meta = more.dataset.sort === "effort" ? "" : fmtDate(p.date);
        const box = `<div class="media">${cardInner({ ...p, meta: p.meta ?? meta })}</div>`;
        const tag = p.link ? "a" : "div";
        const href = p.link ? ` href="${esc(url(p.link))}"` : "";
        return `<${tag} class="more-card${p.image ? " has-image" : ""}"${href}>${box}
          ${p.caption ? `<p class="more-card__caption">${esc(p.caption)}</p>` : ""}</${tag}>`;
      })
      .join("");
  }
})();

/* =========================================================
   EDIT THIS FILE to change project listings.
   Everything that lists projects (sidebar, homepage grid,
   More Projects pages) is built from these two lists.

   image: path from the site root, e.g. "assets/img/synthia/cover.jpg".
          Leave "" to show the gray placeholder.
   ========================================================= */

// "Selected Work" — order here = order in the sidebar and homepage grid.
// Each one links to projects/<slug>.html
window.SELECTED_WORK = [
  { slug: "synthia", title: "Synthia",
    blurb: "visual synthesizer that combines ambient audio with live video to create concert-level visuals in your own home",
    meta: "", image: "" },
  { slug: "cantilevered-deltaxy", title: "Cantilevered DeltaXY Research", blurb: "", meta: "", image: "" },
  { slug: "twofold",              title: "TwoFold",                       blurb: "", meta: "", image: "" },
  { slug: "layer-by-layer",       title: "Layer By Layer",                blurb: "", meta: "", image: "" },
  { slug: "pool-boiling",         title: "Small-scale Pool Boiling Facility", blurb: "", meta: "", image: "" },
  { slug: "pearcat",              title: "PearCat",                       blurb: "", meta: "", image: "" },
  { slug: "mochimash",            title: "MochiMash",                     blurb: "", meta: "", image: "" },
  { slug: "yubbayubba",           title: "YubbaYubba",                    blurb: "", meta: "", image: "" },
  { slug: "en-clair",             title: "en clair",                      blurb: "", meta: "", image: "" },
  { slug: "unit-cell-tessellation", title: "Unit Cell Tesselation",       blurb: "", meta: "", image: "" },
  { slug: "archetype-ai",         title: "Archetype AI",                  blurb: "", meta: "", image: "" },
  { slug: "dme-2026",             title: "DME 2026",                      blurb: "", meta: "", image: "" },
];

// "More Projects" — shown on both More Projects pages.
// date:   "YYYY-MM" (By Date sorts newest first)
// effort: any number, higher = more effort (By Effort sorts highest first)
// link:   optional — a page or external URL; leave "" for no link
window.MORE_PROJECTS = [
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2026-05", effort: 3, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2026-02", effort: 1, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2025-12", effort: 5, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2025-09", effort: 2, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2025-06", effort: 4, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2025-03", effort: 2, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2024-11", effort: 3, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2024-08", effort: 1, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2024-05", effort: 4, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2024-02", effort: 2, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2023-10", effort: 5, image: "", link: "" },
  { title: "Project title", blurb: "", caption: "Short description of the project.", date: "2023-06", effort: 1, image: "", link: "" },
];

// Contact links used in the sidebar and About page
window.CONTACT = {
  linkedin: "https://www.linkedin.com/in/YOUR-HANDLE",   // TODO: your LinkedIn URL
  email: "you@example.com",                              // TODO: the email you want public
  resume: "assets/Joshua-Rivera-Camacho-Resume.pdf",     // put your PDF at this path
};

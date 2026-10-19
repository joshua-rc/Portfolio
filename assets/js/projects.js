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
    blurb: "A visual synthesizer that turns ambient audio and live video into audio-reactive, concert-level visuals in your home.",
    meta: "2025", image: "assets/img/covers/synthia.jpg" },
  { slug: "cantilevered-deltaxy", title: "Cantilevered DeltaXY Research", blurb: "Undergraduate research on a novel 3D printer movement system that fits a 120 mm build area into 127 mm of shelf width — part of co-authored research awarded Best Paper at ACM CHI 2026.", meta: "", image: "assets/img/covers/cantilevered-deltaxy.jpg" },
  { slug: "twofold",              title: "TwoFold",                       blurb: "An entirely analog camera using cyanotyping techniques that opens to make photograms and closes to take photographs.", meta: "", image: "assets/img/covers/twofold.jpg" },
  { slug: "layer-by-layer",       title: "Layer By Layer",                blurb: "Experiment design, execution, and data anaylsis of a beam-bending study testing whether what we know about 3D-printed parts holds up beyond standard test samples.", meta: "", image: "assets/img/covers/layer-by-layer.jpg" },
  { slug: "pool-boiling",         title: "Small-scale Pool Boiling Facility",
    navTitle: "Small-scale Pool\nBoiling Facility",   // line break used in the left menu
    blurb: "An experiment vessel that mimics boiling with gas bubbles and a perforated heater to study how bubble agitation drives heat transfer.", meta: "", image: "assets/img/covers/pool-boiling.jpg" },
  { slug: "pearcat",              title: "PearCat",                       blurb: "A competition robot that had to be redesigned mid-build — and still won the class prize for most complex mechanisms.", meta: "", image: "assets/img/covers/pearcat.jpg" },
  { slug: "mochimash",            title: "MochiMash",                     blurb: "A two-player rhythm game inspired by traditional mochi pounding: one player folds, the other pounds, and both have to stay on beat.", meta: "", image: "assets/img/covers/mochimash.jpg" },
  { slug: "yubbayubba",           title: "YubbaYubba",                    blurb: "50+ identical yo-yos -- plus some exclusive colorways -- designed for mass manufacturing as a homage to the iconic Hubba Bubba bubble gum.", meta: "", image: "assets/img/covers/yubbayubba.jpg" },
  { slug: "en-clair",             title: "en clair",                      blurb: "A handheld device that retranslates the world your hear through filters you desire — because nothing is ever in plain language.", meta: "", image: "assets/img/covers/en-clair.jpg" },
  { slug: "unit-cell-tessellation", title: "Unit Cell Tessellation",      blurb: "A stiffness-optimized metamaterial, printed at the micron scale with two-photon lithography and crushed inside an electron microscope.", meta: "", image: "assets/img/covers/unit-cell-tessellation.jpg" },
  { slug: "archetype-ai",         title: "Archetype AI",                  blurb: "", meta: "", image: "assets/img/covers/archetype-ai.jpg" },
  { slug: "dme-2026",             title: "DME 2026",                      blurb: "Redesigning a first-year robot build challenge that hadn't changed since 2016 — for 30+ students, many building for the first time.", meta: "", image: "assets/img/covers/dme-2026.jpg" },
];

// "More Projects" — shown on both More Projects pages.
// date:   "YYYY-MM" (By Date sorts newest first)
// effort: any number, higher = more effort (By Effort sorts highest first)
// link:   optional — a page or external URL; leave "" for no link
window.MORE_PROJECTS = [
  {"title": "4.02A Drawing Machine", "blurb": "", "caption": "A \"misdrawing machine\" that draws — or perhaps rolls — the lines between collaboration and competition. With Christian Tavera.", "date": "2024-01", "dateLabel": "January 2024", "effort": 0, "image": "", "link": ""},
  {"title": "Totems", "blurb": "", "caption": "A lobby-scale inflatable intervention designed to disrupt \"elephant paths\" — the shortcuts people wear into a space. With Edison Peguero Rosario and Christian Tavera.", "date": "2024-01", "dateLabel": "January 2024", "effort": 0, "image": "", "link": ""},
  {"title": "Plates", "blurb": "", "caption": "An homage to my culture through my deepest connection to it: food. Hand-formed pottery drawing heavily on Talavera, barro rojo, and Capula pottery styles.", "date": "2025-03", "dateLabel": "Spring 2025", "effort": 0, "image": "", "link": ""},
  {"title": "MITES Architecture Project", "blurb": "", "caption": "An introduction to Mongean projection, representing 3D forms through 2D drawing planes. For MITES Semester '22 Architecture Design.", "date": "2022-09", "dateLabel": "Fall 2022", "effort": 0, "image": "", "link": ""},
  {"title": "Clay Hands", "blurb": "", "caption": "A pair of helping hands to hold my jewelry, since my own hands misplaced a piece one too many times.", "date": "2025-03", "dateLabel": "Spring 2025", "effort": 0, "image": "", "link": ""},
  {"title": "2.00t Drawing Machine", "blurb": "", "caption": "A pen plotter that draws using polar coordinates — the project that introduced me to CAD and electromechanical systems. With Daniel Odenthal and Lama Diriyeh.", "date": "2024-03", "dateLabel": "Spring 2024", "effort": 0, "image": "", "link": ""},
  {"title": "4.02A Laser Cut", "blurb": "", "caption": "A 2.5D laser-cut composition designed to create the illusion of weight and depth.", "date": "2024-01", "dateLabel": "January 2024", "effort": 0, "image": "", "link": ""},
  {"title": "Ribcage Shirt", "blurb": "", "caption": "My first major sewing project. It taught me a lot about sewing — and warped my sense of time so badly that I haven't let myself sit back down at the machine for too long since.", "date": "2025-09", "dateLabel": "Fall 2025", "effort": 0, "image": "", "link": ""},
  {"title": "Speakers", "blurb": "", "caption": "My favorite project from my freshman-year seminar and perhaps any workshop ever. An introduction to soldering.", "date": "2023-09", "dateLabel": "Fall 2023", "effort": 0, "image": "", "link": ""},
  {"title": "Glasswork", "blurb": "", "caption": "Stained glass mosaics and glass flamework, mostly made as gifts.", "date": "2026-03", "dateLabel": "Spring 2026", "effort": 0, "image": "", "link": ""},
  {"title": "Linoleum Block Printing", "blurb": "", "caption": "An introduction to engraving, in preparation for a later metalwork project.", "date": "2026-09", "dateLabel": "Fall 2026", "effort": 0, "image": "", "link": ""}
];

// Contact links used in the sidebar and About page
window.CONTACT = {
  linkedin: "https://www.linkedin.com/in/YOUR-HANDLE",   // TODO: your LinkedIn URL
  email: "you@example.com",                              // TODO: the email you want public
  resume: "assets/Joshua-Rivera-Camacho-Resume.pdf",     // put your PDF at this path
};

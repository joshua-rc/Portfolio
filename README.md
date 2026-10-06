# joshuariveracamacho.com

Plain HTML/CSS/JS portfolio built from the Figma file *Portfolio Page Templates*. No build step: open `index.html` in a browser to preview.

## Pages

| File | Figma frame |
|---|---|
| `index.html` | Selected Work (Homepage) |
| `more-projects-by-date.html` / `more-projects-by-effort.html` | More Projects (by date / by effort) |
| `about.html` | About Me |
| `projects/<slug>.html` | Project Page (one per Selected Work project) |
| `projects/_template.html` | Blank project page to copy for new projects |

## Editing content

- **Project lists** (sidebar, homepage cards, More Projects cards): `assets/js/projects.js`. Order, titles, blurbs, cover images, dates and effort scores all live there.
- **Contact links** (LinkedIn, email, resume): the `CONTACT` block at the bottom of `assets/js/projects.js`. Put your resume PDF at `assets/Joshua-Rivera-Camacho-Resume.pdf`.
- **Project write-ups**: edit the HTML in `projects/<slug>.html`. The sidebar's section index is built automatically from each `<section id="..." data-nav="...">`.
- **Images**: put them in `assets/img/<slug>/` and drop an `<img>` inside any gray placeholder:
  `<figure class="media"><img src="../assets/img/synthia/hero.jpg" alt="Synthia prototype"></figure>`
  Export photos as WebP or JPG at about 2000 px wide; keep each under a few MB.
- **Colors, type sizes, spacing**: `assets/css/style.css`. Sizes are written in Figma pixels (on the 2560 px canvas) times `--s`, so `calc(var(--s) * 36)` is the 36 px text from Figma.

## Deploying on GitHub Pages

1. Create a repo (e.g. `portfolio`) and push these files to the `main` branch.
2. Repo **Settings → Pages**: Source = *Deploy from a branch*, Branch = `main`, folder `/ (root)`.
3. The `CNAME` file already contains `joshuariveracamacho.com`. In Settings → Pages, enter the same domain under *Custom domain*.
4. At your domain registrar, replace the Adobe Portfolio DNS records with:
   - `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME` for `www` → `<your-github-username>.github.io`
5. Once the site loads on your domain, tick **Enforce HTTPS**, then cancel Adobe Portfolio.

# Notes for Claude

This is Arnav Kumar Tripathy's personal website. It's a static site built by `build.py` (Python + Jinja2 + PyYAML + Markdown) and deployed by GitHub Actions to GitHub Pages at www.arnavtripathy.com.

## How it's organised

- **Content.** All content lives in `content/` and is edited by the owner through Pages CMS (`.pages.yml`). When you add a content field, add it to `.pages.yml` too, and keep existing field names stable.
- **Templates.** Templates are in `templates/` and extend `base.html`.
  - Links and media paths must go through `{{ base }}` or the `url` filter, so the site also works under a sub-path.
  - Macros are imported `with context`.
- **Project pages.** Each project page is generated as `design-<slug>.html` from `content/projects/<slug>.md`.
- **Web apps.** The tools live in their own GitHub repos and are published by Cloudflare Pages at standalone addresses, so shared links never show this site: Thematis (repo `Thematis`, https://thematis.pages.dev/) and Graphyzo (repo `Graphyzo`, https://graphyzo.pages.dev/). Update a tool in its own repo, never here. `apps/<name>/` is copied unchanged into `_site/<name>/` and now only holds redirect pages, so old links (`/thematis/`, `/graphyzo/`, and Graphyzo's old names `/vizify/`, `/dataviz-now/`) forward to the standalone addresses. The Tools page links (`content/tools.yml`) point to the standalone addresses.
- **Categories.** Project categories are defined in `CATEGORIES` in `build.py`, and their colours are in `assets/styles.css` (`--t-*`).

## Design system

- Swiss modernist: white ground, Hanken Grotesk, a 12-column label|content grid, black top bar.
- Colours:
  - Red #E0381C for marks.
  - #C42D12 for red text.
  - Cobalt #2349C9 (`--teal`) for every hover.
- Page headings end with a red square plus a cobalt square diagonally above it.

## Owner's standing preferences

- Keep headings small. Minimum text sizes are 15px for secondary text and 16px for reading text.
- No page descriptions or ledes under headings.
- Never fabricate content. Empty fields are never shown on the live site: no "To add" prompts, no empty image placeholders. Art & Craft and Tools hide themselves until they have content.
- Pages always open at the top. Keep the smooth page transitions and the once-per-visit loader.

## Checking your work

Run `python3 build.py`, then open `_site/` in a browser.

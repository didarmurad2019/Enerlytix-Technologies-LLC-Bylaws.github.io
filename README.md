# Enerlytix Technologies, LLC — Website

Static site for GitHub Pages: https://didarmurad2019.github.io/Enerlytix-Technologies-LLC.github.io/

## Publish (first time)
1. Create / open the repository **Enerlytix-Technologies-LLC.github.io** on GitHub.
2. Upload **all files from this folder** (keep the folder structure; include the hidden `.nojekyll` and `.github`).
3. Settings → Pages → Source: *Deploy from a branch* → Branch: `main`, folder `/ (root)` → Save.
4. Wait ~1 minute, then open the site URL above.

## Maintain
| Task | How |
|---|---|
| Edit bylaws text | Edit `content/bylaws.md` (keep the `# ARTICLE …` / `**1.1 Title**` format). |
| Regenerate pages + PDF | `pip install -r tools/requirements.txt` then `python tools/build.py`. |
| Automatic rebuild | Pushing a change to `content/bylaws.md` runs `.github/workflows/build.yml`, which rebuilds and commits `index.html`, `bylaws.html` and the PDF. |
| Refresh pictures | `python tools/make_images.py` (colours/text are at the top of the script). |
| Fill in placeholders | Search `content/bylaws.md` for "To be determined" / "To be completed" (members, ownership, state, agent) before execution. |

## Structure
```
index.html  bylaws.html  404.html  sitemap.xml  robots.txt  .nojekyll
assets/css/style.css   assets/js/main.js
assets/images/         logo, favicon, 4 illustrations, social card
assets/downloads/      bylaws PDF + Markdown
content/bylaws.md      single source of truth
tools/                 build.py, make_images.py, requirements.txt
.github/workflows/     automatic rebuild
```
Bylaws page: search, contents navigation, **Download PDF**, **Create PDF / Print** (browser print → Save as PDF), Markdown download, copy link, per-clause deep links.

Note: the bylaws are a template with open placeholders; have counsel review before adoption.

#!/usr/bin/env python3
"""Rebuilds index.html, bylaws.html, 404.html, the PDF, sitemap.xml from content/bylaws.md.
Run:  python tools/build.py    (needs reportlab)"""
import re, html, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://didarmurad2019.github.io/Enerlytix-Technologies-LLC.github.io/"
SRC = ROOT / "content" / "bylaws.md"
PDF_NAME = "Enerlytix-Technologies-LLC-Bylaws.pdf"
TODAY = datetime.date.today().isoformat()

# ───────────────────────── parsing ─────────────────────────
def inline(t):
    t = html.escape(t.replace("\r", ""), quote=False)
    t = re.sub(r"_{3,}", "\u2009", t) if False else t
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', t)
    return t

SMALL = {"and", "of", "to", "the", "in", "for", "with"}
KEEP = {"IESST": "IESST", "ICRI-STE": "ICRI-STE", "LLC": "LLC", "AI": "AI"}
def titlecase(s):
    out = []
    for i, w in enumerate(s.split()):
        out.append(KEEP.get(w, w.lower() if (w.lower() in SMALL and i) else w.capitalize()))
    return " ".join(out)

def parse(text):
    lines = [l.rstrip() for l in text.replace("\r", "").split("\n")]
    meta, front, secs, cur = [], {}, [], None
    i = 0
    while i < len(lines) and not lines[i].startswith("# PREAMBLE"):
        l = lines[i]
        m = re.match(r"\*\*(.+?):\*\*\s*(.+)", l)
        if m: meta.append((m.group(1), m.group(2).strip()))
        elif l.startswith("# "): front["title"] = l[2:]
        elif l.startswith("## "): front["company"] = l[3:]
        elif l.startswith("**") and l.endswith("**"): front["tagline"] = l.strip("*")
        i += 1
    block = None
    def flush():
        nonlocal block
        if block and cur is not None: cur["blocks"].append(block)
        block = None
    while i < len(lines):
        l = lines[i]; i += 1
        if l.startswith("# "):
            flush()
            head = l[2:].strip()
            m = re.match(r"ARTICLE ([IVXL]+) — (.+)", head)
            m2 = re.match(r"SCHEDULE ([AB]) — (.+)", head)
            if m: kicker, title, sid = f"Article {m.group(1)}", titlecase(m.group(2)), f"article-{m.group(1).lower()}"
            elif m2: kicker, title, sid = f"Schedule {m2.group(1)}", titlecase(m2.group(2)), f"schedule-{m2.group(1).lower()}"
            else: kicker, title, sid = "", titlecase(head), re.sub(r"\W+", "-", head.lower()).strip("-")
            cur = {"id": sid, "kicker": kicker, "title": title, "blocks": []}; secs.append(cur)
            continue
        if cur is None or l.strip() in ("", "---"):
            flush(); continue
        m = re.match(r"^\*\*(\d+\.\d+) (.+)\*\*$", l)
        if m:
            flush(); cur["blocks"].append({"t": "clause", "num": m.group(1), "title": m.group(2)}); continue
        if l.startswith("|"):
            if not block or block["t"] != "table": flush(); block = {"t": "table", "rows": []}
            if not re.match(r"^\|[\s\-:|]+\|$", l):
                block["rows"].append([c.strip() for c in l.strip("|").split("|")])
            continue
        for t, pat in (("ul", r"^- (.+)"), ("ol", r"^\d+\. (.+)"), ("sub", r"^[a-z]\. (.+)")):
            m = re.match(pat, l)
            if m:
                if not block or block["t"] != t: flush(); block = {"t": t, "items": []}
                block["items"].append(m.group(1)); break
        else:
            flush(); cur["blocks"].append({"t": "p", "text": l.strip()})
    flush()
    return meta, front, secs

# ───────────────────────── html ─────────────────────────
SIG = re.compile(r"_{4,}")
def itx(t):  # inline for HTML with signature lines
    return SIG.sub('<span class="sigline"></span>', inline(t))

def render_blocks(blocks, sid):
    out, open_clause = [], False
    for b in blocks:
        t = b["t"]
        if t == "clause":
            if open_clause: out.append("</div>")
            cid = "c" + b["num"].replace(".", "-")
            out.append(f'<div class="clause" id="{cid}"><h3><a class="num" href="#{cid}" aria-label="Link to clause {b["num"]}">{b["num"]}</a>'
                       f'<span>{html.escape(b["title"])}</span></h3>')
            open_clause = True
        elif t == "p":
            cls = ' class="sig"' if "____" in b["text"] else ""
            out.append(f"<p{cls}>{itx(b['text'])}</p>")
        elif t in ("ul", "ol"):
            out.append(f"<{t}>" + "".join(f"<li>{inline(x)}</li>" for x in b["items"]) + f"</{t}>")
        elif t == "sub":
            out.append('<ol class="sub" type="a">' + "".join(f"<li>{inline(x)}</li>" for x in b["items"]) + "</ol>")
        elif t == "table":
            r = b["rows"]
            out.append('<div class="tablewrap"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in r[0]) +
                       "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in r[1:]) +
                       "</tbody></table></div>")
    if open_clause: out.append("</div>")
    return "\n".join(out)

HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title><meta name="description" content="{desc}">
<meta name="theme-color" content="#08222F">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}assets/images/og-image.png"><meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="assets/images/favicon.svg"><link rel="icon" sizes="32x32" href="assets/images/favicon-32.png">
<link rel="apple-touch-icon" href="assets/images/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Inter:wght@400;500;600&display=swap">
<link rel="stylesheet" href="assets/css/style.css"></head>"""

def header(active):
    nav = [("index.html", "Home", "home"), ("index.html#build", "What we build", ""), ("index.html#affiliation", "Research", ""),
           ("bylaws.html", "Bylaws", "bylaws")]
    links = "".join(f'<a href="{h}"{" aria-current=page" if a == active else ""}>{n}</a>' for h, n, a in nav)
    return f"""<body class="{active}"><a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap bar"><a class="brand" href="index.html"><img src="assets/images/logo.svg" alt="" width="36" height="36"><span>Enerlytix<small>Technologies, LLC</small></span></a>
<button class="menu" aria-expanded="false" aria-controls="nav">Menu</button><nav id="nav" aria-label="Main">{links}
<a class="btn small" href="assets/downloads/{PDF_NAME}" download>Download PDF</a></nav></div></header>"""

def footer(front):
    return f"""<footer><div class="wrap foot"><div><strong>Enerlytix Technologies, LLC</strong><p>{html.escape(front.get('tagline',''))}</p></div>
<div><a href="index.html">Home</a><a href="bylaws.html">Bylaws</a><a href="assets/downloads/{PDF_NAME}" download>Bylaws (PDF)</a><a href="assets/downloads/bylaws.md" download>Bylaws (Markdown)</a></div>
<div><p>© {datetime.date.today().year} Enerlytix Technologies, LLC. All rights reserved.</p><p class="fine">Research affiliation: IESST Lab, ICRI-STE. The Company and IESST Lab remain institutionally and legally distinct.</p></div></div></footer>
<script src="assets/js/main.js" defer></script></body></html>"""

def bylaws_page(meta, front, secs):
    toc = "".join(f'<li><a href="#{s["id"]}"><span>{s["kicker"] or "&nbsp;"}</span>{html.escape(s["title"])}</a></li>' for s in secs)
    info = "".join(f"<div><dt>{html.escape(k)}</dt><dd>{inline(v)}</dd></div>" for k, v in meta
                   if k in ("Document Version", "Legal Entity", "Entity Type", "Effective Date", "Governing Jurisdiction"))
    body = "".join(
        f'<section class="article" id="{s["id"]}"><header>{f"<p class=kicker>{s["kicker"]}</p>" if s["kicker"] else ""}<h2>{html.escape(s["title"])}</h2></header>'
        f'{render_blocks(s["blocks"], s["id"])}</section>' for s in secs)
    return (HEAD.format(title="Bylaws & Operating Governance Framework | Enerlytix Technologies, LLC",
                        desc="Read, search, download or print the complete Bylaws and Operating Governance Framework of Enerlytix Technologies, LLC.",
                        url=SITE + "bylaws.html", site=SITE) + header("bylaws") + f"""
<main id="main"><div class="wrap doc-head"><p class="kicker">Governing document</p><h1>Bylaws and Operating Governance Framework</h1>
<dl class="docinfo">{info}</dl>
<div class="actions" role="group" aria-label="Document actions">
<a class="btn" href="assets/downloads/{PDF_NAME}" download>Download PDF</a>
<button class="btn ghost" id="print" type="button">Create PDF / Print</button>
<a class="btn ghost" href="assets/downloads/bylaws.md" download>Markdown</a>
<button class="btn ghost" id="share" type="button">Copy link</button></div>
<p class="hint">“Create PDF / Print” opens your browser’s print dialog — choose <em>Save as PDF</em> as the destination.</p></div>
<div class="wrap doc-grid"><aside class="toc" aria-label="Contents"><label class="search"><span class="sr">Search the bylaws</span>
<input id="q" type="search" placeholder="Search clauses…" autocomplete="off"></label><p id="count" class="count" aria-live="polite"></p>
<nav><ol>{toc}</ol></nav></aside>
<article class="doc" id="doc">{body}<p id="none" class="none" hidden>No clauses match your search.</p></article></div></main>""" + footer(front))

def home_page(meta, front, secs):
    arts = [s for s in secs if s["id"].startswith("article")]
    clauses = sum(1 for s in arts for b in s["blocks"] if b["t"] == "clause")
    objectives = next(b for s in secs if s["id"] == "article-ii" for b in s["blocks"] if b["t"] == "ol")["items"]
    reserved = next(b for s in secs if s["id"] == "schedule-b" for b in s["blocks"] if b["t"] == "ol")["items"]
    a3 = next(s for s in secs if s["id"] == "article-iii")["blocks"]
    focus = [(a3[i]["title"], a3[i + 1]["text"]) for i in range(len(a3) - 1) if a3[i]["t"] == "clause" and a3[i + 1]["t"] == "p"][:8]
    focus_html = "".join(f'<li><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></li>' for t, d in focus)
    vision = next(b["text"] for s in secs if s["id"] == "article-ii" for b in s["blocks"] if b["t"] == "p" and b["text"].startswith("To become"))
    mission = next(b["text"] for s in secs if s["id"] == "article-ii" for b in s["blocks"] if b["t"] == "p" and b["text"].startswith("To transform"))
    return (HEAD.format(title="Enerlytix Technologies, LLC | Intelligent Energy. Advanced Analytics.",
                        desc="Enerlytix Technologies, LLC develops AI-powered energy analytics, renewable-energy forecasting and smart-grid technologies.",
                        url=SITE, site=SITE) + header("home") + f"""
<main id="main"><section class="hero"><div class="wrap hero-grid"><div class="hero-copy">
<h1>Energy data, turned into decisions.</h1>
<p class="lede">Enerlytix Technologies builds AI-powered analytics for renewable generation, smart grids and energy storage — software that makes intelligent energy systems practical and scalable.</p>
<div class="actions"><a class="btn" href="#build">What we build</a><a class="btn ghost-light" href="bylaws.html">Read our bylaws</a></div></div>
<figure class="chart" aria-label="Illustrative chart of forecast versus observed solar generation over a day">
<svg viewBox="0 0 560 340" role="img"><title>Illustrative forecast band and observed generation</title>
<defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#12B5A0" stop-opacity=".45"/><stop offset="1" stop-color="#12B5A0" stop-opacity="0"/></linearGradient></defs>
<g stroke="#fff" stroke-opacity=".12"><path d="M40 40H540M40 110H540M40 180H540M40 250H540"/><path d="M40 40V290M165 40V290M290 40V290M415 40V290M540 40V290"/></g>
<path d="M40 290C140 290 190 60 290 60S440 290 540 290V290H40Z" fill="url(#g)"/>
<path class="draw" d="M40 290C140 290 190 60 290 60S440 290 540 290" fill="none" stroke="#12B5A0" stroke-width="4" pathLength="1"/>
<path class="draw d2" d="M40 288C120 286 170 96 250 78S330 82 380 150 470 280 540 286" fill="none" stroke="#F5A623" stroke-width="3" stroke-dasharray="1 0" pathLength="1"/>
<g fill="#C9DAD7" font-size="12" font-family="Inter,sans-serif"><text x="40" y="314">06:00</text><text x="272" y="314">12:00</text><text x="500" y="314">18:00</text><text x="40" y="28">Generation</text></g></svg>
<figcaption><span class="k t"></span>Forecast <span class="k a"></span>Observed <em>Illustrative</em></figcaption></figure></div></section>

<section class="band" id="build"><div class="wrap split"><div class="sticky"><h2>What we build</h2><p>{html.escape(vision)}</p></div>
<ul class="rows">{focus_html}</ul></div></section>

<section class="gallery"><div class="wrap"><h2>Research priorities in view</h2><p class="sub">Computational intelligence applied across the energy value chain.</p>
<div class="mosaic"><figure class="m1"><img src="assets/images/forecast.png" alt="Forecast band with observed generation points" loading="lazy" width="1200" height="800"></figure>
<figure class="m2"><img src="assets/images/smartgrid.png" alt="Network of distributed energy nodes" loading="lazy" width="1200" height="800"></figure>
<figure class="m3"><img src="assets/images/battery.png" alt="Battery cells at different charge levels" loading="lazy" width="1200" height="800"></figure>
<figure class="m4"><img src="assets/images/ai-network.png" alt="Layered neural network diagram" loading="lazy" width="1200" height="800"></figure></div></div></section>

<section class="mission"><div class="wrap"><p class="big">{html.escape(mission)}</p></div></section>

<section class="band" id="governance"><div class="wrap"><h2>Governed by a published framework</h2>
<dl class="figures"><div><dt>{len(arts)}</dt><dd>Articles of governance</dd></div><div><dt>{clauses}</dt><dd>Numbered clauses</dd></div>
<div><dt>{len(objectives)}</dt><dd>Strategic objectives</dd></div><div><dt>{len(reserved)}</dt><dd>Matters reserved for Member approval</dd></div></dl>
<div class="principles"><p><strong>Responsible AI.</strong> Reliability, transparency, fairness, security and human oversight (Art. XI).</p>
<p><strong>Data and cybersecurity.</strong> Lawful data handling and safeguards built into every platform.</p>
<p><strong>Intellectual property.</strong> Clear ownership, contributor agreements and licensing (Art. X).</p>
<p><strong>Accountability.</strong> Financial controls, annual review and records access for Members (Arts. IX, XIV).</p></div></div></section>

<section class="band alt" id="affiliation"><div class="wrap split"><div><h2>Research affiliation</h2></div><div>
<p>Enerlytix may collaborate with the Intelligent Energy Systems &amp; Sustainable Technologies (IESST) Lab, operating under ICRI-STE, on approved research in AI-powered optimisation, renewable forecasting and smart-grid intelligence.</p>
<p>The Company and IESST Lab remain institutionally and legally distinct, and collaboration is governed by written agreements covering IP, confidentiality and publication rights (Art. VIII).</p></div></div></section>

<section class="cta"><div class="wrap"><h2>Read the full Bylaws</h2><p>Search every clause, download the PDF, or print your own copy.</p>
<div class="actions"><a class="btn" href="bylaws.html">Open the Bylaws</a><a class="btn ghost-light" href="assets/downloads/{PDF_NAME}" download>Download PDF</a></div></div></section></main>""" + footer(front))

def page_404(front):
    return (HEAD.format(title="Page not found | Enerlytix Technologies, LLC", desc="Page not found", url=SITE, site=SITE).replace('href="assets', 'href="/assets') if False else
            HEAD.format(title="Page not found | Enerlytix Technologies, LLC", desc="Page not found", url=SITE, site=SITE)) + header("x") + \
        '<main id="main" class="wrap nf"><h1>Page not found</h1><p>The page you requested does not exist.</p><a class="btn" href="index.html">Back to home</a></main>' + footer(front)

# ───────────────────────── pdf ─────────────────────────
def build_pdf(meta, front, secs, path):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle as PS
    from reportlab.lib.units import inch
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Table,
                                    TableStyle, ListFlowable, ListItem, KeepTogether, NextPageTemplate)
    INK, TEAL, GREY = colors.HexColor("#08222F"), colors.HexColor("#0E8F7E"), colors.HexColor("#5B6B72")
    body = PS("b", fontName="Times-Roman", fontSize=10.5, leading=15, spaceAfter=6, textColor=colors.HexColor("#1B2A30"))
    sty = dict(
        body=body, h1=PS("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=INK, spaceBefore=18, spaceAfter=8, keepWithNext=1),
        kick=PS("k", fontName="Helvetica-Bold", fontSize=8.5, textColor=TEAL, spaceBefore=16, leading=11, keepWithNext=1),
        h3=PS("h3", fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=INK, spaceBefore=8, spaceAfter=3, keepWithNext=1),
        toc=PS("t", fontName="Helvetica", fontSize=10, leading=17, textColor=INK))
    def foot(c, d):
        c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(GREY)
        c.drawString(inch, 0.55 * inch, "Enerlytix Technologies, LLC — Bylaws and Operating Governance Framework")
        c.drawRightString(letter[0] - inch, 0.55 * inch, f"Page {d.page}")
        c.setStrokeColor(colors.HexColor("#D5E0DE")); c.line(inch, 0.75 * inch, letter[0] - inch, 0.75 * inch); c.restoreState()
    def cover(c, d):
        c.saveState(); c.setFillColor(INK); c.rect(0, 0, *letter, fill=1, stroke=0)
        c.drawImage(str(ROOT / "assets/images/logo-512.png"), inch, letter[1] - 2.1 * inch, 80, 80)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 38); c.drawString(inch, 5.6 * inch, "Bylaws and")
        c.drawString(inch, 5.6 * inch - 46, "Operating Governance"); c.drawString(inch, 5.6 * inch - 92, "Framework")
        c.setFont("Helvetica", 17); c.setFillColor(colors.HexColor("#12B5A0")); c.drawString(inch, 3.1 * inch, "Enerlytix Technologies, LLC")
        c.setFillColor(colors.HexColor("#C9DAD7")); c.setFont("Helvetica", 11)
        c.drawString(inch, 2.7 * inch, front.get("tagline", ""))
        c.drawString(inch, 1.5 * inch, "Document Version " + dict(meta).get("Document Version", ""))
        c.drawString(inch, 1.25 * inch, SITE); c.restoreState()
    doc = BaseDocTemplate(str(path), pagesize=letter, title="Enerlytix Technologies, LLC — Bylaws and Operating Governance Framework",
                          author="Enerlytix Technologies, LLC")
    fr = Frame(inch, inch, letter[0] - 2 * inch, letter[1] - 1.7 * inch, id="f")
    doc.addPageTemplates([PageTemplate("cover", [Frame(0, 0, *letter)], onPage=cover),
                          PageTemplate("main", [fr], onPage=foot)])
    P = lambda t, s: Paragraph(SIG.sub("_" * 34, inline(t)), s)
    st = [NextPageTemplate("main"), PageBreak(), Paragraph("Contents", sty["h1"])]
    st += [Paragraph(f'{s["kicker"] + " — " if s["kicker"] else ""}{html.escape(s["title"])}', sty["toc"]) for s in secs]
    st += [PageBreak(), Paragraph("Document Information", sty["h1"])]
    st += [P(f"**{k}:** {v}", body) for k, v in meta]
    for s in secs:
        st.append(Paragraph(s["kicker"].upper(), sty["kick"]) if s["kicker"] else Spacer(1, 10))
        st.append(Paragraph(html.escape(s["title"]), sty["h1"]))
        for b in s["blocks"]:
            t = b["t"]
            if t == "clause": st.append(Paragraph(f'{b["num"]}&nbsp;&nbsp;{html.escape(b["title"])}', sty["h3"]))
            elif t == "p": st.append(P(b["text"], body))
            elif t in ("ul", "ol", "sub"):
                kw = dict(bulletType="bullet", start="•") if t == "ul" else dict(bulletType="1" if t == "ol" else "a", bulletFormat="%s.")
                st.append(ListFlowable([ListItem(P(x, body), leftIndent=22) for x in b["items"]], leftIndent=22, bulletFontName="Times-Roman", **kw))
                st.append(Spacer(1, 4))
            elif t == "table":
                data = [[Paragraph(inline(c), PS("c", fontName="Helvetica-Bold" if r == 0 else "Helvetica", fontSize=9, leading=12,
                          textColor=colors.white if r == 0 else INK)) for c in row] for r, row in enumerate(b["rows"])]
                tb = Table(data, repeatRows=1, hAlign="LEFT")
                tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), INK), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#C9D6D3")),
                                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F6")]),
                                        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
                st += [tb, Spacer(1, 8)]
    doc.build(st)

# ───────────────────────── main ─────────────────────────
def main():
    text = SRC.read_text(encoding="utf-8")
    meta, front, secs = parse(text)
    (ROOT / "assets/downloads").mkdir(parents=True, exist_ok=True)
    (ROOT / "assets/downloads/bylaws.md").write_text(text.replace("\r\n", "\n"), encoding="utf-8")
    (ROOT / "index.html").write_text(home_page(meta, front, secs), encoding="utf-8")
    (ROOT / "bylaws.html").write_text(bylaws_page(meta, front, secs), encoding="utf-8")
    (ROOT / "404.html").write_text(page_404(front), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
        "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{TODAY}</lastmod></url>" for p in ("", "bylaws.html")) + "</urlset>")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n")
    (ROOT / ".nojekyll").write_text("")
    build_pdf(meta, front, secs, ROOT / "assets/downloads" / PDF_NAME)
    print("built:", len(secs), "sections")

if __name__ == "__main__":
    main()

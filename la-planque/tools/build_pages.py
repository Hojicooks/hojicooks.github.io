#!/usr/bin/env python3
"""Génère une page HTML par fiche de La Planque (pour Google et le partage), les pages
de catégories, le sommaire et le sitemap, à partir de la base Supabase (lecture publique).
Usage : python3 la-planque/tools/build_pages.py [--local fichier.json]
Écrit uniquement dans la-planque/<catégorie>/, la-planque/fiches/ et la-planque/sitemap.xml."""
import json, os, re, sys, shutil, html, unicodedata, urllib.request, hashlib, base64
from datetime import datetime, timezone, timedelta

SITE = "https://hojicooks.github.io/la-planque/"
SUPABASE = "https://sonpigelysgbfvbeotgj.supabase.co"
KEY = "sb_publishable_yzD2ln5tGuEZZyYttiFCWA__bK-4psf"  # clé publique, lecture seule
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# col en base -> (dossier URL, module de l'app, nom, titre de catégorie, intro)
CATS = [
  ("tips", "astuces", "astuces", "Astuce", "Astuces GTA 6", "Les astuces et l'actu de GTA VI, vérifiées et sourcées, en français."),
  ("money", "argent", "argent", "Argent", "Gagner de l'argent dans GTA 6", "Les méthodes pour faire de l'argent dans GTA VI, avec niveau requis et risque police."),
  ("codes", "codes", "codes", "Code", "Codes de triche GTA 6", "Les codes de triche de GTA VI avec les touches PlayStation et Xbox."),
  ("vehicles", "vehicules", "voitures", "Véhicule", "Véhicules de GTA 6", "Les véhicules confirmés de GTA VI : catégorie, sécurité, valeur de revente."),
  ("wildlife", "faune", "faune", "Animal", "Faune et pêche dans GTA 6", "Les animaux de Leonida : où les trouver et à quoi faire attention."),
  ("places", "lieux", "lieux", "Lieu", "Lieux de GTA 6", "Planques, garages, boutiques et lieux connus de Leonida, classés par région."),
  ("lexicon", "lexique", "lexique", "Lexique", "Lexique de GTA 6", "Les applis, objets et mécaniques de GTA VI, expliqués un par un."),
  ("completion", "100-pourcent", "cent", "Objectif", "Objectif 100 % de GTA 6", "Trophées, collectibles et activités à faire pour le 100 % de GTA VI, sans spoiler."),
]
WIKI = {"vehicles", "wildlife", "places", "lexicon", "codes", "completion"}
# Mesure d'audience anonyme (sans cookie ni identifiant) : une page vue = un appel à la fonction hit de la base.
HIT_JS = ('(function(){try{if(sessionStorage.getItem("pl_hit_"+location.pathname))return;sessionStorage.setItem("pl_hit_"+location.pathname,"1")}catch(e){}'
          'var p="page-"+location.pathname.replace(/^\\/la-planque\\//,"").replace(/\\/$/,"").toLowerCase().replace(/[^a-z0-9_-]+/g,"-").slice(0,85);'
          'var r=document.referrer||"",u=navigator.userAgent||"",s=/musical_ly|BytedanceWebview|TikTok/i.test(u)||/tiktok\\./.test(r)?"tiktok":/google\\./.test(r)?"google":!r?"direct":"autre";'
          'try{fetch("https://sonpigelysgbfvbeotgj.supabase.co/rest/v1/rpc/hit",{method:"POST",keepalive:true,headers:{"apikey":"sb_publishable_yzD2ln5tGuEZZyYttiFCWA__bK-4psf","Content-Type":"application/json"},body:JSON.stringify({p_path:p,p_src:s})}).catch(function(){})}catch(e){}})()')
HIT_SHA = "sha256-" + base64.b64encode(hashlib.sha256(HIT_JS.encode("utf-8")).digest()).decode()
REFS = {}
SEC = {1: "Aucune", 2: "Alarme", 3: "Clé électronique", 4: "Antidémarrage"}
RISK = {0: "Aucun", 1: "Faible", 2: "Moyen", 3: "Élevé"}
STATUS = {"verifie": "Vérifié", "a-confirmer": "À confirmer", "rumeur": "Rumeur", "archive": "Expiré"}
PS = {"X": "✕", "O": "○", "CARRE": "□", "TRIANGLE": "△", "HAUT": "↑", "BAS": "↓", "GAUCHE": "←", "DROITE": "→"}
XB = {"X": "A", "O": "B", "CARRE": "X", "TRIANGLE": "Y", "R1": "RB", "R2": "RT", "L1": "LB", "L2": "LT", "R3": "RS", "L3": "LS",
      "HAUT": "↑", "BAS": "↓", "GAUCHE": "←", "DROITE": "→"}
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

def esc(s): return html.escape(str(s or ""), quote=True)

def load(local=None):
    if local:
        raw = json.load(open(local, encoding="utf-8"))
        if isinstance(raw, dict):
            return [{"col": c, "id": r["id"], "data": r["data"]} for c, rows in raw.items() for r in rows]
        return raw
    req = urllib.request.Request(SUPABASE + "/rest/v1/fiches?select=col,id,data&order=col,id",
                                 headers={"apikey": KEY, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def title_of(d): return d.get("title") or d.get("name") or "Sans titre"

def summary_of(col, d):
    for k in ("short", "how", "body", "notes", "tip", "requires", "spawn", "habitat", "area"):
        if d.get(k):
            t = re.sub(r"\s+", " ", re.sub(r"^\d+\.\s*", "", plain(d[k]))).strip()
            return t[:155].rsplit(" ", 1)[0] + "…" if len(t) > 158 else t
    return "Fiche GTA VI sur La Planque, le guide en français."


# ---- liens entre fiches (même logique que l'app) ----
MODSEG = {c[2]: c[1] for c in CATS}
COLMOD = {c[0]: c[2] for c in CATS}
LKSKIP = {"pic", "rat", "chat", "autre"}
MANUAL = re.compile(r"\[\[([^\]|]{1,80})\|([^\]]{1,120})\]\]")
IDX, WHERE = [], {}

def norm(t): return "".join(c for c in unicodedata.normalize("NFD", str(t or "").lower()) if not unicodedata.combining(c))
def nmap(t): return "".join((lambda n: n if len(n) == 1 else ch.lower())(norm(ch)) for ch in t)
def isw(c): return bool(c) and bool(re.match(r"[a-z0-9]", c))
def plain(t): return MANUAL.sub(lambda m: m.group(1), str(t or ""))

def text_of(d): return "\n\n".join(str(x) for x in (d.get("steps"), d.get("body") or d.get("notes") or d.get("tip") or d.get("how")) if x)

def build_refs(rows):
    REFS.clear()
    for r in rows:
        if r["data"].get("status") == "exemple" or r["col"] not in COLMOD: continue
        ctx = {"self": r["id"], "used": set()}
        linkify(text_of(r["data"]), ctx)
        for fid in ctx["used"]:
            if fid: REFS.setdefault(fid, []).append(r)

def build_index(rows):
    IDX.clear(); WHERE.clear()
    for r in rows:
        mod, d = COLMOD.get(r["col"]), r["data"]
        if not mod or d.get("status") == "exemple": continue
        WHERE[r["id"]] = mod
        def add(n, cs):
            n = str(n).strip()
            if len(n) < 3: return
            k = n if cs else norm(n)
            if not cs and k in LKSKIP: return
            IDX.append((k, cs, mod, r["id"]))
        n = re.sub(r"\s*\(.*?\)\s*", " ", title_of(d)).strip()
        if mod in ("faune", "lieux", "voitures", "lexique"):
            if len(n) >= 4: add(n, False)
            if mod == "voitures":
                md = " ".join(n.split(" ")[1:])
                if len(md) >= 5: add(md, True)
        for x in re.split(r"[,;\n]", str(d.get("links") or "")): add(x, False)
    IDX.sort(key=lambda e: -len(e[0]))

def lk_a(txt, mod, fid):
    href = f"../../{MODSEG[mod]}/" + (f"{fid}/" if fid else "")
    return f'<a class="xl" href="{esc(href)}">{esc(txt)}</a>'

def auto_links(t, ctx):
    if ctx.get("manual"): return esc(t)
    nt, hits = nmap(t), []
    for k, cs, mod, fid in IDX:
        if fid == ctx["self"] or fid in ctx["used"]: continue
        hay, frm = (t if cs else nt), 0
        while True:
            i = hay.find(k, frm)
            if i < 0: break
            frm, j = i + 1, i + len(k)
            if i > 0 and isw(nt[i - 1]): continue
            if not cs and j < len(nt) and nt[j] in "sx" and not (j + 1 < len(nt) and isw(nt[j + 1])): j += 1
            if j < len(nt) and isw(nt[j]): continue
            if any(i < b and j > a for a, b, _, _ in hits): continue
            hits.append((i, j, mod, fid)); ctx["used"].add(fid); break
    out, p = [], 0
    for a, b, mod, fid in sorted(hits):
        out.append(esc(t[p:a])); out.append(lk_a(t[a:b], mod, fid)); p = b
    out.append(esc(t[p:]))
    return "".join(out)

def linkify(text, ctx):
    t, out, last = str(text or ""), [], 0
    if MANUAL.search(t): ctx["manual"] = True
    for m in MANUAL.finditer(t):
        out.append(auto_links(t[last:m.start()], ctx))
        tg, tm, tid = m.group(2).strip(), None, None
        if tg in MODSEG: tm = tg
        elif "/" in tg and tg.split("/")[0] in MODSEG: tm, tid = tg.split("/", 1)
        else: tid, tm = tg, WHERE.get(tg)
        if tm and (not tid or tid in WHERE): out.append(lk_a(m.group(1), tm, tid)); ctx["used"].add(tid)
        else: out.append(esc(m.group(1)))
        last = m.end()
    out.append(auto_links(t[last:], ctx))
    return "".join(out)

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
def fr_date(ms):
    t = datetime.fromtimestamp(int(ms) / 1000, timezone.utc).astimezone(timezone(timedelta(hours=1)))
    return f"{t.day} {MOIS[t.month - 1]} {t.year}"

def thin(col, d):
    if d.get("status") in ("exemple", "archive") or d.get("movedTo"): return True
    if col == "vehicles" and not d.get("value"): return True
    return False

def stats(col, d):
    s = []
    if col == "money":
        s += [("Gain par heure", f"{d['perHour']:,} $".replace(",", " ") if d.get("perHour") else None),
              ("Niveau", d.get("level")), ("Risque police", RISK.get(d.get("risk") or 0)), ("Il te faut", d.get("requires"))]
    elif col == "vehicles":
        s += [("Revente", f"{d['value']:,} $".replace(",", " ") if d.get("value") else None), ("Catégorie", d.get("cls")),
              ("Disponibilité", d.get("access") if d.get("access") not in (None, "", "Standard") else None),
              ("Sécurité", SEC.get(d.get("security"))), ("Outil", d.get("tool") if d.get("tool") not in (None, "", "Inconnu") else None),
              ("Traceur GPS", ("Oui" if d.get("tracker") else "Non") if d.get("security") else None),
              ("Région", d.get("region") if d.get("region") not in (None, "", "Inconnu") else None), ("Où le trouver", d.get("spawn"))]
    elif col == "wildlife":
        s += [("Région", d.get("region") if d.get("region") not in (None, "", "Inconnu") else None), ("Habitat", d.get("habitat")),
              ("Rareté", d.get("rarity")), ("Type", d.get("kind"))]
    elif col == "places":
        s += [("Type", d.get("kind")), ("Région", d.get("region") if d.get("region") not in (None, "", "Inconnu") else None),
              ("Quartier", d.get("area")), ("Disponibilité", d.get("access") if d.get("access") not in (None, "", "Standard") else None)]
    elif col == "codes":
        s += [("Par téléphone", d.get("phone"))]
    elif col == "completion":
        s += [("Catégorie", d.get("group")), ("Au total", d.get("total")), ("Pour le 100 %", d.get("need")), ("Trophée", d.get("trophy"))]
    elif col == "lexicon":
        s += [("Catégorie", d.get("cat")), ("Où le trouver", d.get("where"))]
    return [(k, v) for k, v in s if v not in (None, "")]

def paras(text, ctx):
    ps = [p.strip() for p in re.split(r"\n\s*\n", str(text or "")) if p.strip()]
    if len(ps) > 1 and all(re.match(r"^\d+\.\s", p) for p in ps):
        return "<ol>" + "".join(f"<li>{linkify(re.sub(r'^\d+\.\s*', '', p), ctx)}</li>" for p in ps) + "</ol>"
    return "".join(f"<p>{linkify(p, ctx)}</p>" for p in ps)

CSS = """:root{--bg:#1d1532;--card:#271e42;--line:#43375f;--fg:#fbf3ff;--mute:#bdb0d8;--accent:#ff7eb3;--teal:#6fe3d4;--ok:#5fe0a0;--gold:#ffc768;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 Overpass,system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--teal)}.w{max-width:720px;margin:0 auto;padding:0 max(16px,env(safe-area-inset-left,0px)) 48px max(16px,env(safe-area-inset-right,0px))}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 0;border-bottom:1px solid var(--line);margin-bottom:18px}
.logo{display:flex;align-items:center;gap:9px;font-family:Yellowtail,"Brush Script MT",cursive;font-size:28px;line-height:1;color:var(--fg);text-decoration:none}.logo svg{width:40px;height:24px;color:var(--accent);transform:rotate(-8deg)}
.btn{display:inline-flex;align-items:center;justify-content:center;height:44px;padding:0 18px;border-radius:12px;background:var(--accent);color:#3a0a22;font-weight:700;text-decoration:none}
.btn.sec{background:var(--card);color:var(--fg);border:1px solid var(--line)}
.w p{white-space:pre-line}.crumb{font-size:13px;color:var(--mute)}.crumb a{color:var(--mute)}
h1{font-size:clamp(26px,6vw,34px);line-height:1.2;margin:6px 0 10px;text-wrap:balance}h2{font-size:18px;margin:28px 0 10px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}.tag{font-size:12.5px;font-weight:600;padding:3px 9px;border-radius:8px;background:var(--card);color:var(--mute)}
.tag.ok{color:var(--ok)}.tag.gold{color:var(--gold)}.tag.rum{color:var(--accent)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin:14px 0}.stat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px 12px}
.stat small{display:block;font-size:12.5px;font-weight:600;color:var(--mute)}.stat b{font-size:16px}
ol{padding-left:22px}li{margin:6px 0}.combo{font-size:22px;letter-spacing:.08em;font-weight:700}
.box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:16px 0}
.shot{margin:14px 0 6px;border-radius:16px;overflow:hidden;aspect-ratio:16/9;background:var(--card)}.shot img{width:100%;height:100%;object-fit:cover;display:block}.credit{font-size:12.5px;color:var(--mute);margin:0 0 14px}.credit a{color:var(--mute)}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin:26px 0}
ul.list{list-style:none;padding:0;margin:0;display:grid;gap:8px}ul.list a{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;color:var(--fg);text-decoration:none;font-weight:600}
ul.list small{display:block;color:var(--mute);font-weight:400;font-size:13px}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);font-size:12.5px;color:var(--mute)}"""

RIMG = "https://www.rockstargames.com/VI/_next/static/media/"
WIMG = ("https://upload.wikimedia.org/wikipedia/commons/", "https://thumb.wikimedia.org/wikipedia/commons/")
def ext_img(d):
    u = d.get("imageUrl")
    ok = isinstance(u, str) and (u.startswith(RIMG) or u.startswith(WIMG)) and not re.search(r"[?#\"'<>\s]", u)
    return u if ok else None

def img_src(u, w):
    return f"{u}?akim=1&imwidth={w}" if u.startswith(RIMG) else u

def page(title, desc, url, body, noindex=False, rel="", og=None):
    robots = '<meta name="robots" content="noindex,follow">\n' if noindex else ""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="article"><meta property="og:site_name" content="La Planque"><meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(url)}">{f'<meta property="og:image" content="{esc(og)}">' if og else f'<meta property="og:image" content="{SITE}og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1d1532">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;800&family=Yellowtail&display=swap"><link rel="icon" href="{rel}icon-192.png"><link rel="apple-touch-icon" href="{rel}apple-touch-icon.png">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https://www.rockstargames.com https://upload.wikimedia.org https://thumb.wikimedia.org; script-src '{HIT_SHA}'; connect-src https://sonpigelysgbfvbeotgj.supabase.co; base-uri 'none'">
<style>{CSS}</style>
</head>
<body><div class="w">
<header><a class="logo" href="{rel}"><svg viewBox="0 0 44 26" aria-hidden="true"><path d="M3.5 13 11 3.5h28a3 3 0 0 1 3 3v13a3 3 0 0 1-3 3H11z" fill="currentColor"/><circle cx="11.2" cy="13" r="2.4" fill="#1d1532"/><text x="27.5" y="18.3" text-anchor="middle" font-family="Overpass,system-ui,sans-serif" font-weight="800" font-size="14" fill="#3a0a22">6</text></svg>La Planque</a><a class="btn" href="{rel}">Ouvrir l'app</a></header>
{body}
<footer>La Planque, guide de fan non officiel, sans lien avec Rockstar Games ni Take-Two Interactive. <a href="{rel}#confidentialite">Mentions légales et confidentialité</a></footer>\n<script>{HIT_JS}</script>
</div></body></html>
"""

def fiche_html(cat, row, siblings):
    col, seg, mod, label, ctitle, _ = cat
    d, fid = row["data"], row["id"]
    t = title_of(d)
    ctx = {"self": fid, "used": set(), "manual": bool(MANUAL.search(text_of(d)))}
    url = f"{SITE}{seg}/{fid}/"
    tags = [f'<span class="tag">{esc(label)}</span>']
    if d.get("theme"): tags.append(f'<span class="tag">{esc(d["theme"])}</span>')
    st = STATUS.get(d.get("status"))
    if st: tags.append(f'<span class="tag { {"verifie":"ok","rumeur":"rum"}.get(d.get("status"),"gold") }">{esc(st)}</span>')
    b = [f'<div class="crumb"><a href="../../">La Planque</a> › <a href="../">{esc(ctitle)}</a></div>',
         f"<h1>{esc(t)}</h1>", '<div class="tags">' + "".join(tags) + "</div>"]
    c_ts, u_ts = d.get("createdAt") or d.get("updatedAt"), d.get("updatedAt")
    if c_ts:
        line = "Ajoutée le " + fr_date(c_ts)
        if u_ts and u_ts - c_ts > 3600000: line += ", mise à jour le " + fr_date(u_ts)
        b.append(f'<p class="crumb">{esc(line)}.</p>')
    mv = str(d.get("movedTo") or "").split("/")
    if len(mv) == 2 and mv[0] in MODSEG and SAFE_ID.match(mv[1]):
        b.append(f'<div class="box"><b>Cette fiche a été déplacée :</b> <a href="../../{MODSEG[mv[0]]}/{esc(mv[1])}/">voir la nouvelle page</a>.</div>')
    if col == "codes" and d.get("combo"):
        toks = str(d["combo"]).upper().split()
        b.append('<div class="box"><small>PlayStation</small><div class="combo">' + esc(" ".join(PS.get(x, x) for x in toks)) +
                 '</div><small>Xbox</small><div class="combo">' + esc(" ".join(XB.get(x, x) for x in toks)) + "</div></div>")
    xi = ext_img(d)
    if xi:
        rk = xi.startswith(RIMG)
        src = str(d.get("imageSource") or "")
        if rk:
            src = src if src.startswith("https://www.rockstargames.com/") else "https://www.rockstargames.com/VI/media"
            lab, txt = "Image", "capture officielle © Rockstar Games"
        else:
            src = src if src.startswith("https://commons.wikimedia.org/") else "https://commons.wikimedia.org"
            lab, txt = "Photo réelle", d.get("imageCredit") or "Wikimedia Commons"
        b.append(f'<div class="shot"><img src="{esc(img_src(xi, 1024))}" alt="{esc(d.get("imageCaption") or t)}" loading="lazy"></div>'
                 f'<p class="credit">{lab} : <a href="{esc(src)}" rel="noopener">{esc(txt)}</a>{" · " + esc(d["imageCaption"]) if d.get("imageCaption") else ""}</p>')
    s = stats(col, d)
    if col == "lexicon" and d.get("short"): b.append(f'<p class="lead"><b>{esc(d["short"])}</b></p>')
    if s: b.append('<div class="stats">' + "".join(f'<div class="stat"><small>{esc(k)}</small><b>{esc(v)}</b></div>' for k, v in s) + "</div>")
    if col == "money" and d.get("steps"):
        b.append("<h2>Étape par étape</h2><ol>" + "".join(f"<li>{linkify(x.strip(), ctx)}</li>" for x in str(d["steps"]).split("\n") if x.strip()) + "</ol>")
    txt = d.get("body") or d.get("notes") or d.get("tip") or d.get("how")
    if txt: b.append(paras(txt, ctx))
    if d.get("videoUrl") and re.match(r"^https?://", d["videoUrl"]):
        b.append(f'<div class="box"><b>Vidéo à voir : <a href="{esc(d["videoUrl"])}" rel="noopener">{esc(d.get("videoTitle") or "Regarder")}</a></b>'
                 + (f' <small>({esc(d["videoBy"])})</small>' if d.get("videoBy") else "")
                 + (f"<p>{esc(d['videoSummary'])}</p>" if d.get("videoSummary") else "") + "</div>")
    for line in str(d.get("moreVideos") or "").split("\n"):
        pp = [x.strip() for x in line.split("|")]
        if pp and re.match(r"^https?://[^\s\"'<>]+$", pp[0]):
            b.append(f'<div class="box"><b>Vidéo à voir aussi : <a href="{esc(pp[0])}" rel="noopener">{esc(pp[1] if len(pp) > 1 and pp[1] else "Regarder")}</a></b>'
                     + (f' <small>({esc(pp[2])})</small>' if len(pp) > 2 and pp[2] else "") + (f"<p>{esc(pp[3])}</p>" if len(pp) > 3 and pp[3] else "") + "</div>")
    if d.get("source") and re.match(r"^https?://", d["source"]):
        host = re.sub(r"^https?://(www\.)?", "", d["source"]).split("/")[0]
        b.append(f'<p><small>Source : <a href="{esc(d["source"])}" rel="noopener nofollow">{esc(host)}</a></small></p>')
    refs = [x for x in REFS.get(fid, []) if x["id"] != fid] if col in WIKI else []
    if refs:
        segof = {c[0]: c[1] for c in CATS}
        b.append("<h2>Mentionné dans</h2><ul class=\"list\">" + "".join(
            f'<li><a href="../../{segof[x["col"]]}/{esc(x["id"])}/">{esc(title_of(x["data"]))}</a></li>' for x in refs[:8]) + "</ul>")
    b.append(f'<div class="cta"><a class="btn" href="../../#voir-{mod}-{esc(fid)}">Voir dans l\'app</a><a class="btn sec" href="../">{esc(ctitle)}</a></div>')
    others = [r for r in siblings if r["id"] != fid and not thin(col, r["data"])][:6]
    if others:
        b.append("<h2>À voir aussi</h2><ul class=\"list\">" + "".join(
            f'<li><a href="../{esc(r["id"])}/">{esc(title_of(r["data"]))}</a></li>' for r in others) + "</ul>")
    return page(f"{t} – GTA 6 | La Planque", summary_of(col, d), url, "\n".join(b), noindex=thin(col, d), rel="../../", og=img_src(xi, 1280) if xi else None)

def cat_html(cat, rows):
    col, seg, mod, label, ctitle, intro = cat
    items = "".join(f'<li><a href="{esc(r["id"])}/">{esc(title_of(r["data"]))}<small>{esc(summary_of(col, r["data"]))}</small></a></li>'
                    for r in rows if r["data"].get("status") != "exemple")
    body = (f'<div class="crumb"><a href="../">La Planque</a> › <a href="../fiches/">Toutes les fiches</a></div><h1>{esc(ctitle)}</h1><p>{esc(intro)}</p>'
            f'<ul class="list">{items or "<li>Bientôt des fiches ici.</li>"}</ul>'
            f'<div class="cta"><a class="btn" href="../#{mod}">Ouvrir dans l\'app</a></div>')
    return page(f"{ctitle} | La Planque", intro, f"{SITE}{seg}/", body, rel="../")

def hub_html(groups):
    lis = "".join(f'<li><a href="../{c[1]}/">{esc(c[4])}<small>{len([r for r in rows if r["data"].get("status")!="exemple"])} fiches</small></a></li>' for c, rows in groups)
    intro = "Toutes les fiches de La Planque, le guide GTA VI en français : astuces, argent, codes, véhicules, faune, lieux et lexique du jeu."
    body = f'<div class="crumb"><a href="../">La Planque</a></div><h1>Toutes les fiches GTA 6</h1><p>{esc(intro)}</p><ul class="list">{lis}</ul>'
    return page("Toutes les fiches GTA 6 | La Planque", intro, f"{SITE}fiches/", body, rel="../")

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and open(path, encoding="utf-8").read() == content: return False
    open(path, "w", encoding="utf-8").write(content); return True

def main():
    local = sys.argv[sys.argv.index("--local") + 1] if "--local" in sys.argv else None
    rows = [r for r in load(local) if isinstance(r.get("data"), dict) and SAFE_ID.match(str(r.get("id", "")))]
    build_index(rows)
    build_refs(rows)
    changed, urls, groups = 0, [(SITE, None), (SITE + "fiches/", None)], []
    for cat in CATS:
        col, seg = cat[0], cat[1]
        crow = sorted([r for r in rows if r["col"] == col], key=lambda r: (not r["data"].get("prio"), -(r["data"].get("updatedAt") or 0)))
        groups.append((cat, crow))
        base = os.path.join(ROOT, seg)
        keep = set()
        for r in crow:
            if r["data"].get("status") == "exemple": continue
            keep.add(r["id"])
            changed += write(os.path.join(base, r["id"], "index.html"), fiche_html(cat, r, crow))
            if not thin(col, r["data"]):
                ts = r["data"].get("updatedAt")
                urls.append((f"{SITE}{seg}/{r['id']}/", datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m-%d") if ts else None))
        changed += write(os.path.join(base, "index.html"), cat_html(cat, crow))
        urls.append((f"{SITE}{seg}/", None))
        if os.path.isdir(base):
            for name in os.listdir(base):
                p = os.path.join(base, name)
                if os.path.isdir(p) and name not in keep and SAFE_ID.match(name):
                    shutil.rmtree(p); changed += 1
    changed += write(os.path.join(ROOT, "fiches", "index.html"), hub_html(groups))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"  <url><loc>{esc(u)}</loc>{f'<lastmod>{m}</lastmod>' if m else ''}</url>\n" for u, m in urls) + "</urlset>\n"
    changed += write(os.path.join(ROOT, "sitemap.xml"), sm)
    print(f"{len(rows)} fiches lues, {changed} fichiers modifiés, {len(urls)} adresses dans le sitemap")

if __name__ == "__main__":
    main()

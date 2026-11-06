#!/usr/bin/env python3
"""Сборка сайта «Жизнь без долгов».
Запуск:  python3 build.py
Результат — папка dist/, её целиком загружаешь на хостинг.
Новая статья = новый .md файл в content/articles/ (формат — как у существующих)."""
import datetime as dt, json, re, shutil, uuid
from pathlib import Path
import markdown, yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
MONTHS = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
SECTIONS = {"mfc": "Банкротство через МФЦ", "sud": "Судебное банкротство", "posledstviya": "Последствия и имущество",
            "kollektory": "Коллекторы и кредиторы", "mfo": "Микрозаймы и кредиты", "rabota": "Работа и доход при долгах", "varianty": "Другие варианты"}
NOW = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).replace(tzinfo=None, second=0, microsecond=0)  # время по Москве
TODAY = NOW.date()
BUILD = uuid.uuid4().hex[:8]
md = lambda t: markdown.markdown(t, extensions=["tables", "sane_lists"])

def ru_date(d): return f"{d.day} {MONTHS[d.month-1]} {d.year}"
def plain(html): return re.sub(r"<[^>]+>", "", html)

def read_md(path):
    raw = path.read_text(encoding="utf-8")
    _, fm, body = raw.split("---", 2)
    meta = yaml.safe_load(fm)
    meta["html"] = md(body)
    return meta

def org():
    return {"@context": "https://schema.org", "@type": "Organization", "name": cfg["site_name"],
            "url": cfg["site_url"], "logo": cfg["site_url"] + "/assets/logo.png"}

def crumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": cfg["site_url"] + u} for i, (n, u) in enumerate(items)]}

def faq_schema(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]}

def js(objs): return [json.dumps(o, ensure_ascii=False).replace("</", "<\\/") for o in objs]

def write(url, tpl, **ctx):
    out = DIST / url.strip("/") / "index.html" if url != "/404.html" else DIST / "404.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    base = dict(cfg=cfg, url=url, build_id=BUILD, year=TODAY.year, sections=SECTIONS, schema=[], noindex=False)
    base.update(ctx)
    html = env.get_template(tpl).render(**base)
    if future_slugs:   # ссылки на ещё не вышедшие статьи — пока простым текстом
        html = re.sub(r'<a href="/voprosy/(' + "|".join(map(re.escape, future_slugs)) + r')/"[^>]*>(.*?)</a>', r"\2", html, flags=re.S)
    out.write_text(html, encoding="utf-8")
    if not base["noindex"] and url != "/404.html":
        pages.append((url, ctx.get("lastmod", TODAY.isoformat())))

pages = []
shutil.rmtree(DIST, ignore_errors=True)
shutil.copytree(ROOT / "assets", DIST / "assets")
if (ROOT / "root").exists():
    for f in (ROOT / "root").iterdir(): shutil.copy(f, DIST / f.name)   # файлы в корень сайта (подтверждения Яндекс/Google)

# --- статьи
arts = []
scheduled_today, scheduled_later, future_slugs = [], 0, set()
for p in sorted((ROOT / "content/articles").glob("*.md")):
    a = read_md(p)
    if a.get("publish"):   # отложенная публикация: "ГГГГ-ММ-ДД" (09:00) или "ГГГГ-ММ-ДД ЧЧ:ММ" по Москве
        raw = str(a["publish"]).strip()
        pub_dt = dt.datetime.fromisoformat(raw if len(raw) > 10 else raw + " 09:00")
        if pub_dt > NOW: scheduled_later += 1; future_slugs.add(a["slug"]); continue
        if NOW - pub_dt < dt.timedelta(hours=4): scheduled_today.append(f"content/articles/{p.name}")
        a["updated"] = max(pub_dt.date(), a["updated"] if isinstance(a["updated"], dt.date) else dt.date.fromisoformat(str(a["updated"])))
    a["url"] = f"/voprosy/{a['slug']}/"
    upd = a["updated"] if isinstance(a["updated"], dt.date) else dt.date.fromisoformat(str(a["updated"]))
    a["updated"], a["updated_ru"] = upd.isoformat(), ru_date(upd)
    a["short_html"] = md(a["short"])
    if a.get("cta") and a["cta"]["href"] in ("bot", "lead"): a["cta"]["href"] = cfg["lead_url"]
    a["minutes"] = max(2, round(len(plain(a["html"]).split()) / 180))
    arts.append(a)
by_slug = {a["slug"]: a for a in arts}
for a in arts:
    rel = [by_slug[s] for s in a.get("related", []) if s in by_slug]
    rel += [x for x in arts if x["section"] == a["section"] and x is not a and x not in rel]
    article = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["description"],
               "dateModified": a["updated"], "datePublished": str(a.get("published", a["updated"])),
               "author": {"@type": "Organization", "name": cfg["author"]}, "publisher": org(),
               "mainEntityOfPage": cfg["site_url"] + a["url"], "inLanguage": "ru"}
    sch = [article, crumbs([("Главная", "/"), ("Статьи", "/baza/"), (a["title"], a["url"])])]
    if a.get("faq"): sch.append(faq_schema(a["faq"]))
    write(a["url"], "article.html", a=a, related=rel[:4], page_title=f"{a['title']} | {cfg['site_name']}",
          description=a["description"], og_type="article", schema=js(sch), lastmod=a["updated"])

# --- база знаний
groups = {k: [a for a in arts if a["section"] == k] for k in SECTIONS}
write("/baza/", "baza.html", groups=groups, page_title=f"Статьи о банкротстве и долгах | {cfg['site_name']}",
      description="Ответы на вопросы о банкротстве через МФЦ и суд, коллекторах, микрозаймах и последствиях — простым языком.",
      schema=js([crumbs([("Главная", "/"), ("Статьи", "/baza/")])]))

# --- главная
home_faq = [
    {"q": "Можно ли списать долги бесплатно?", "a": "Да, через МФЦ — если долг от 25 000 до 1 000 000 ₽ и приставы закрыли исполнительное производство из-за отсутствия имущества. Судебное банкротство платное."},
    {"q": "Заберут ли единственное жильё?", "a": "Единственное жильё, если оно не в залоге у банка, при банкротстве не забирают. Ипотечную квартиру можно сохранить, если договориться с банком."},
    {"q": "Какие долги не спишут?", "a": "Алименты, возмещение вреда здоровью, долги по зарплате перед работниками, субсидиарную ответственность и долги, возникшие из-за мошенничества."},
    {"q": "Вы юристы?", "a": "Мы — информационный проект. Если нужна помощь с процедурой, с вашего согласия передаём заявку юристу-партнёру, консультация бесплатна."},
]
FEATURED = ["mfo-limit-dvuh-dorogih-zaymov-2026", "bankrotstvo-cherez-mfc-usloviya", "skolko-stoit-bankrotstvo-fizlica", "chto-zaberut-pri-bankrotstve", "kollektory-zvonyat-chto-delat", "uvedomleniya-o-kreditah-na-gosuslugah"]
latest = [by_slug[s] for s in FEATURED if s in by_slug] or arts[:6]
write("/", "index.html", latest=latest, home_faq=home_faq,
      page_title=f"{cfg['site_name']} — банкротство, МФЦ и долги честно и простым языком",
      description="Как списать долги законно: банкротство через МФЦ и через суд, последствия, коллекторы, микрозаймы. Тест «подходит ли банкротство» за 2 минуты.",
      schema=js([org(), {"@context": "https://schema.org", "@type": "WebSite", "name": cfg["site_name"], "url": cfg["site_url"]}, faq_schema(home_faq)]))

# --- тест
write("/test/podhodit-li-bankrotstvo/", "quiz_page.html", updated_ru=ru_date(TODAY),
      page_title=f"Тест: подходит ли вам банкротство — через МФЦ или суд | {cfg['site_name']}",
      description="Ответьте на 4 вопроса и узнайте, подходит ли вам бесплатное банкротство через МФЦ или судебная процедура.",
      schema=js([crumbs([("Главная", "/"), ("Тест", "/test/podhodit-li-bankrotstvo/")])]))

# --- служебные страницы
for p in sorted((ROOT / "content/pages").glob("*.md")):
    pg = read_md(p)
    pg["html"] = pg["html"].replace("{bot_url}", cfg["bot_url"]).replace("{channel_url}", cfg["channel_url"]).replace("{tg_url}", cfg["tg_url"]).replace("{max_url}", cfg["max_url"]) \
        .replace("{email}", cfg["email"]).replace("{legal_line}", cfg["legal_line"]).replace("{site_name}", cfg["site_name"]).replace("{partner_line}", cfg["partner_line"]).replace("{lead_url}", cfg["lead_url"])
    pg["updated_ru"] = ru_date(TODAY) if pg.get("show_updated") else ""
    write(f"/{pg['slug']}/", "page.html", p=pg, page_title=f"{pg['title']} | {cfg['site_name']}",
          description=pg["description"], noindex=pg.get("noindex", False))

write("/404.html", "page.html", p={"title": "Страница не найдена", "html": '<p>Такой страницы нет. Начните с <a href="/">главной</a> или <a href="/baza/">базы знаний</a>.</p>', "updated_ru": ""},
      page_title="Страница не найдена", description="", noindex=True)

# --- sitemap, robots, IndexNow
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
sm += [f"<url><loc>{cfg['site_url']}{u}</loc><lastmod>{m}</lastmod></url>" for u, m in pages]
sm.append("</urlset>")
(DIST / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
(DIST / "robots.txt").write_text(
    "User-agent: *\nAllow: /\n\n# ИИ-ассистенты могут читать и цитировать сайт\nUser-agent: GPTBot\nAllow: /\nUser-agent: OAI-SearchBot\nAllow: /\n"
    "User-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\n\n"
    f"Sitemap: {cfg['site_url']}/sitemap.xml\n", encoding="utf-8")
(DIST / f"{cfg['indexnow_key']}.txt").write_text(cfg["indexnow_key"], encoding="utf-8")
(DIST / "urls.txt").write_text("\n".join(cfg["site_url"] + u for u, _ in pages), encoding="utf-8")
print(f"Готово: {len(pages)} страниц в индексе, {len(arts)} статей → {DIST}")
(DIST / "scheduled_today.txt").write_text("\n".join(scheduled_today), encoding="utf-8")
print(f"Отложенные: сейчас вышло {len(scheduled_today)}, ждут своей даты {scheduled_later}")

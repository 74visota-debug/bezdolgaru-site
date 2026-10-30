#!/usr/bin/env python3
"""Анонс новых статей в Telegram-канал. Запускается GitHub Actions после публикации.
Нужны секреты репозитория: TG_BOT_TOKEN (токен бота-админа канала) и TG_CHAT_ID (например @biznessnul9)."""
import json, os, sys, urllib.parse, urllib.request
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parent.parent
cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
token, chat = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHAT_ID")
if not token or not chat:
    print("TG_BOT_TOKEN / TG_CHAT_ID не заданы — анонс пропущен"); sys.exit(0)
for f in [x for x in sys.argv[1:] if x.endswith(".md")]:
    _, fm, _ = (ROOT / f).read_text(encoding="utf-8").split("---", 2)
    m = yaml.safe_load(fm)
    url = f"{cfg['site_url']}/voprosy/{m['slug']}/"
    text = f"<b>{m['title']}</b>\n\n{m['short'].strip()}\n\n👉 <a href=\"{url}\">Читать полностью</a>"
    data = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "HTML"}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=20) as r:
        print(f, "→", json.loads(r.read())["ok"])

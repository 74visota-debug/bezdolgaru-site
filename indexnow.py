#!/usr/bin/env python3
"""Сообщить Яндексу (и Bing) о новых и обновлённых страницах через IndexNow.
Запускать ПОСЛЕ загрузки сайта на хостинг:  python3 indexnow.py
Без аргументов отправляет все страницы из dist/urls.txt.
Можно передать конкретные адреса:  python3 indexnow.py https://site.ru/voprosy/novaya-statya/"""
import json, sys, urllib.request
from pathlib import Path
import yaml
ROOT = Path(__file__).parent
cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
urls = sys.argv[1:] or (ROOT / "dist/urls.txt").read_text(encoding="utf-8").split()
host = cfg["site_url"].split("//", 1)[1]
body = json.dumps({"host": host, "key": cfg["indexnow_key"],
                   "keyLocation": f"{cfg['site_url']}/{cfg['indexnow_key']}.txt", "urlList": urls}).encode()
for endpoint in ("https://yandex.com/indexnow", "https://api.indexnow.org/indexnow"):
    req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: print(endpoint, "→", r.status)
    except Exception as e: print(endpoint, "→ ошибка:", e)

# -*- coding: utf-8 -*-
"""
extract-content.py
==================
從已有 <!--EDIT:key--> 標記的 index.html 中提取所有內容到 content.json。
執行後你可以編輯 content.json，再執行 python update-content.py 套用。
"""
import json, re, sys, os
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

HTML_FILE    = "index.html"
CONTENT_FILE = "content.json"

with open(HTML_FILE, encoding="utf-8") as f:
    html = f.read()

pattern = re.compile(r'<!--EDIT:(.*?)-->(.*?)<!--/EDIT:\1-->', re.DOTALL)
matches = pattern.findall(html)

if not matches:
    print("❌ 找不到任何 <!--EDIT:--> 標記")
    sys.exit(1)

content = {}
for key, value in matches:
    content[key] = value.strip()

with open(CONTENT_FILE, "w", encoding="utf-8") as f:
    json.dump(content, f, ensure_ascii=False, indent=2)

print(f"✅ 提取完成！共找到 {len(content)} 個可編輯欄位 → {CONTENT_FILE}")
print()
for k, v in content.items():
    short = re.sub(r'<[^>]+>', '', v)[:40].replace('\n', ' ')
    print(f"  [{k}] = {short}")

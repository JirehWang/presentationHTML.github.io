# -*- coding: utf-8 -*-
"""
convert-markers.py
==================
將 index.html 中的 <!--EDIT:key-->text<!--/EDIT:key--> 
轉換為 <span data-edit-key="key">text</span>
這樣頁面上的文字就可以直接被 JS 鎖定並設為可編輯。
只需執行一次。
"""
import re, sys, os
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

HTML_FILE = "index.html"

with open(HTML_FILE, encoding="utf-8") as f:
    html = f.read()

pattern = re.compile(r'<!--EDIT:(.*?)-->(.*?)<!--/EDIT:\1-->', re.DOTALL)

count = len(pattern.findall(html))
html = pattern.sub(lambda m: f'<span data-edit-key="{m.group(1)}">{m.group(2)}</span>', html)

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 轉換完成！共轉換 {count} 個 EDIT 標記 → data-edit-key span")

# -*- coding: utf-8 -*-
"""
update-content.py
=================
兩個模式：

  python update-content.py --init
      掃描 index.html，在所有可編輯文字外層加上 <!--EDIT:key--> 標記，
      並產生 content.json（可供你編輯）。
      ⚠️  只需要執行一次。之後不要再執行 --init，否則會重複加標記。

  python update-content.py
      讀取 content.json，把所有 key 的內容套回 index.html。
      這是你日常使用的指令。

流程：
  1. 第一次：python update-content.py --init
  2. 打開 content.json 編輯內容
  3. python update-content.py
  4. git add index.html content.json && git commit -m "..." && git push
"""

import json
import re
import sys
import os

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


HTML_FILE    = "index.html"
CONTENT_FILE = "content.json"

# ─────────────────────────────────────────────────────────────────────────────
# 哪些元素要被標記（init 模式用）
# 每個規則：(regex pattern, key_prefix)
# pattern 必須含有一個 capture group 捕捉「內層 HTML」
# ─────────────────────────────────────────────────────────────────────────────
TAGGABLE_PATTERNS = [
    # slide header titles (h1 in header)
    (r'(<h1 id="header-title"[^>]*>)(.*?)(</h1>)', "header-title"),
    # slide h2 titles
    (r'(<h2\b[^>]*class="[^"]*font-bold[^"]*"[^>]*>)(.*?)(</h2>)', None),
    # slide h3 subtitles
    (r'(<h3\b[^>]*class="[^"]*font-bold[^"]*"[^>]*>)(.*?)(</h3>)', None),
    # p subtitles
    (r'(<p\b[^>]*class="[^"]*text-stone-500[^"]*"[^>]*>)(.*?)(</p>)', None),
    # badge spans (e.g. slide category labels)
    (r'(<span\b[^>]*class="[^"]*tracking-wider[^"]*"[^>]*>)([^<]{4,})(</span>)', None),
    # bold div cards (node titles etc.)
    (r'(<div\b[^>]*class="[^"]*font-bold[^"]*"[^>]*>)((?:(?!<div).){6,}?)(</div>)', None),
]

def sanitize_key(text):
    """Turn text into a valid key string."""
    text = re.sub(r'<[^>]+>', '', text)   # strip tags
    text = text.strip()[:40]
    text = re.sub(r'[^\w\u4e00-\u9fff]+', '-', text)
    return text.strip('-').lower()

# ─────────────────────────────────────────────────────────────────────────────
# INIT MODE
# ─────────────────────────────────────────────────────────────────────────────

def init_mode():
    if not os.path.exists(HTML_FILE):
        print(f"❌ 找不到 {HTML_FILE}")
        sys.exit(1)

    with open(HTML_FILE, encoding="utf-8") as f:
        html = f.read()

    # Check if already initialized
    if "<!--EDIT:" in html:
        print("⚠️  HTML 已含有 <!--EDIT:--> 標記，請勿重複執行 --init")
        print("   直接編輯 content.json 後執行 python update-content.py 即可")
        sys.exit(0)

    content = {}
    key_counter = {}

    def make_unique_key(base):
        key_counter[base] = key_counter.get(base, 0) + 1
        return f"{base}-{key_counter[base]}" if key_counter[base] > 1 else base

    # ── Find slide sections to give keys context ──────────────────────────────
    # We'll process slide by slide
    slide_boundaries = list(re.finditer(r'<div id="slide-(\d+)"', html))
    slide_ranges = []
    for i, m in enumerate(slide_boundaries):
        start = m.start()
        end   = slide_boundaries[i+1].start() if i+1 < len(slide_boundaries) else len(html)
        slide_ranges.append((int(m.group(1)), start, end))

    def slide_for_pos(pos):
        for snum, sstart, send in slide_ranges:
            if sstart <= pos < send:
                return snum
        return 0

    def replacer(m, prefix=None):
        inner = m.group(2)
        slide = slide_for_pos(m.start())
        base  = f"s{slide}-{sanitize_key(inner)}" if slide else sanitize_key(inner)
        if prefix:
            base = prefix
        key = make_unique_key(base)
        content[key] = inner
        return f"{m.group(1)}<!--EDIT:{key}-->{inner}<!--/EDIT:{key}-->{m.group(3)}"

    # Apply patterns
    for pattern, prefix in TAGGABLE_PATTERNS:
        html = re.sub(pattern, lambda m, p=prefix: replacer(m, p), html, flags=re.DOTALL)

    # Write modified HTML
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    # Write content.json
    with open(CONTENT_FILE, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print(f"✅ 初始化完成！")
    print(f"   • 標記了 {len(content)} 個可編輯欄位")
    print(f"   • 已產生 {CONTENT_FILE}（請打開此檔案編輯內容）")
    print(f"   • 已更新 {HTML_FILE}（加入 <!--EDIT:--> 標記）")
    print()
    print("📋 下一步：")
    print("   1. 打開 content.json 編輯文字內容")
    print("   2. 執行 python update-content.py")

# ─────────────────────────────────────────────────────────────────────────────
# APPLY MODE（預設）
# ─────────────────────────────────────────────────────────────────────────────

def apply_mode():
    if not os.path.exists(CONTENT_FILE):
        print(f"❌ 找不到 {CONTENT_FILE}，請先執行：python update-content.py --init")
        sys.exit(1)
    if not os.path.exists(HTML_FILE):
        print(f"❌ 找不到 {HTML_FILE}")
        sys.exit(1)

    with open(CONTENT_FILE, encoding="utf-8") as f:
        content = json.load(f)

    with open(HTML_FILE, encoding="utf-8") as f:
        html = f.read()

    if "<!--EDIT:" not in html:
        print("❌ HTML 中找不到 <!--EDIT:--> 標記，請先執行：python update-content.py --init")
        sys.exit(1)

    updated = 0
    not_found = []

    for key, value in content.items():
        pattern = rf'(<!--EDIT:{re.escape(key)}-->)(.*?)(<!--/EDIT:{re.escape(key)}-->)'
        new_block = f'<!--EDIT:{key}-->{value}<!--/EDIT:{key}-->'
        new_html, count = re.subn(pattern, new_block, html, flags=re.DOTALL)
        if count > 0:
            html = new_html
            updated += 1
        else:
            not_found.append(key)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 套用完成！更新了 {updated} 個欄位")

    if not_found:
        print(f"\n⚠️  以下 key 在 HTML 中找不到對應標記（可能已被刪除）：")
        for k in not_found:
            print(f"   - {k}")

    print()
    print("📋 下一步（推送到 GitHub）：")
    print('   git add index.html content.json')
    print('   git commit -m "update: edit slide content"')
    print('   git push')

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--init" in sys.argv:
        init_mode()
    else:
        apply_mode()

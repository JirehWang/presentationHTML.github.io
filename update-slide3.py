# -*- coding: utf-8 -*-
"""
update-slide3.py
================
讀取 slide3-config.json，自動更新 index.html 中的：
  1. Slide 3 的所有節點 HTML（按 config 順序排列）
  2. connections 陣列（根據 config 中的節點順序自動推導）

使用方式：
  python update-slide3.py

說明：
  - 編輯 slide3-config.json 即可修改節點內容與順序
  - 執行此腳本後，index.html 會自動更新，不需要手動修改 HTML
"""

import json
import re
import sys

CONFIG_FILE = "slide3-config.json"
HTML_FILE   = "index.html"

# ── 載入 config ──────────────────────────────────────────────────────────────
with open(CONFIG_FILE, encoding="utf-8") as f:
    cfg = json.load(f)

with open(HTML_FILE, encoding="utf-8") as f:
    html = f.read()

# ── 輔助函式 ─────────────────────────────────────────────────────────────────

THEME_COLORS = {
    "green":  {"glow": "glow-green",  "text": "emerald", "border": "emerald-500/25",
               "badge_bg": "bg-emerald-50", "badge_border": "border-emerald-200",
               "badge_text": "text-emerald-700"},
    "blue":   {"glow": "glow-blue",   "text": "blue",    "border": "blue-500/25",
               "badge_bg": "bg-blue-50",    "badge_border": "border-blue-200",
               "badge_text": "text-blue-700"},
    "orange": {"glow": "glow-orange", "text": "amber",   "border": "amber-500/25",
               "badge_bg": "bg-amber-50",   "badge_border": "border-amber-200",
               "badge_text": "text-amber-700"},
}

def make_normal_card(node, theme):
    c = THEME_COLORS[theme]
    nid  = node["id"]
    step = node["step_label"]
    icon = node["icon"]
    title = node["title"]
    sub  = node["subtitle"]
    sub_html = f'\n                    <div class="text-[9px] text-stone-450 mt-1">{sub}</div>' if sub else ""
    return f'''                  <div id="node-{nid}" class="glass-card {c["glow"]} w-48 p-4 rounded-xl cursor-pointer flex flex-col justify-between h-28 {c["border"]}" onclick="handleNodeClick(event, '{nid}')">
                    <div class="flex justify-between items-start">
                      <span class="text-[10px] {c["badge_text"]} font-semibold tracking-wider">{step}</span>
                      <i data-lucide="{icon}" class="w-3.5 h-3.5 {c["badge_text"]}"></i>
                    </div>
                    <div class="font-bold text-xs text-stone-850 mt-2 leading-relaxed">{title}</div>{sub_html}
                  </div>'''

def make_decision_card(node, theme):
    c = THEME_COLORS[theme]
    nid  = node["id"]
    step = node["step_label"]
    icon = node["icon"]
    title = node["title"]
    sub  = node["subtitle"]
    sub_html = f'\n                    <div class="text-[9px] text-stone-450 text-right mt-1">{sub}</div>' if sub else ""
    return f'''                  <div id="node-{nid}" class="glass-card {c["glow"]} w-44 p-4 rounded-xl cursor-pointer flex flex-col justify-between h-28 {c["border"]}" onclick="handleNodeClick(event, '{nid}')">
                    <div class="flex justify-between items-start">
                      <span class="text-[10px] {c["badge_text"]} font-semibold tracking-wider">{step}</span>
                      <i data-lucide="{icon}" class="w-3.5 h-3.5 {c["badge_text"]}"></i>
                    </div>
                    <div class="font-bold text-sm text-stone-850 mt-2 text-center">{title}</div>{sub_html}
                  </div>'''

def make_outcome_card(node, theme, yes=True):
    c = THEME_COLORS[theme]
    nid   = node["id"]
    step  = node["step_label"]
    icon  = node["icon"]
    title = node["title"]
    if yes:
        label_color = "text-emerald-800"
        icon_color  = "text-emerald-700"
        title_color = "text-stone-800"
    else:
        label_color = "text-stone-500"
        icon_color  = "text-stone-500"
        title_color = "text-stone-750"
    return f'''                    <div id="node-{nid}" class="glass-card {c["glow"]} w-52 p-3.5 rounded-xl cursor-pointer flex flex-col justify-between h-[58px] {c["border"].replace('25','20')}" onclick="handleNodeClick(event, '{nid}')">
                      <div class="flex justify-between items-center">
                        <div class="flex flex-col">
                          <span class="text-[9px] {label_color} font-bold">{step}</span>
                          <span class="text-xs font-bold {title_color}">{title}</span>
                        </div>
                        <i data-lucide="{icon}" class="w-3 h-3 {icon_color} shrink-0 ml-1"></i>
                      </div>
                    </div>'''

ARROW = '                  <i data-lucide="arrow-right" class="w-4 h-4 text-stone-300"></i>'

def build_block_html(block_key):
    """Build HTML for block1, block2, or block3."""
    blk   = cfg[block_key]
    theme = blk["theme"]
    c     = THEME_COLORS[theme]
    label = blk["label"]
    nodes = blk["nodes"]

    # Map block_key -> section id
    sec_id = block_key.replace("block", "block-")  # block1 -> block-1

    lines = []
    lines.append(f'              <section id="{sec_id}" class="glass-panel section-{sec_id[-1]} rounded-2xl p-7 relative transition-opacity duration-300" onclick="handleBlockClick(event, \'{sec_id}\')">')
    lines.append(f'                <div class="absolute -top-3 left-6 px-3 py-0.5 {c["badge_bg"]} border {c["badge_border"]} {c["badge_text"]} text-[10px] font-semibold rounded-full tracking-wider">')
    lines.append(f'                  {label}')
    lines.append(f'                </div>')
    lines.append(f'                ')
    lines.append(f'                <div class="flex items-center space-x-8 pt-2">')

    # Group outcome pairs so they render in a stacked column
    i = 0
    while i < len(nodes):
        node = nodes[i]
        ntype = node.get("type", "normal")

        # Check if next node is also an outcome (pair them in a column)
        next_node = nodes[i+1] if i+1 < len(nodes) else None
        next_type = next_node.get("type", "") if next_node else ""

        if ntype in ("outcome-yes", "outcome-no") and next_type in ("outcome-yes", "outcome-no"):
            # Stacked pair column
            lines.append('                  <div class="flex flex-col space-y-4">')
            lines.append(make_outcome_card(node, theme, yes=(ntype=="outcome-yes")))
            lines.append('                    ')
            lines.append(make_outcome_card(next_node, theme, yes=(next_type=="outcome-yes")))
            lines.append('                  </div>')
            i += 2
        elif ntype == "decision":
            lines.append(make_decision_card(node, theme))
            lines.append(ARROW)
            i += 1
        else:
            lines.append(make_normal_card(node, theme))
            if i < len(nodes) - 1:
                next_ntype = nodes[i+1].get("type","") if i+1 < len(nodes) else ""
                if next_ntype not in ("outcome-yes","outcome-no"):
                    lines.append(ARROW)
                else:
                    lines.append(ARROW)
            i += 1

    # Special case: if last rendered was normal/decision and outcomes follow, arrow already added above
    lines.append('                </div>')
    lines.append('              </section>')

    return "\n".join(lines)


def build_connections(blocks):
    """Auto-derive connections from config node ordering."""
    conns = []
    colors = {"green": "#5f725a", "blue": "#5b7086", "orange": "#c68a4c", "loop": "#7c726a"}

    for bkey in ["block1", "block2", "block3"]:
        blk   = cfg[bkey]
        theme = blk["theme"]
        col   = colors[theme]
        nodes = blk["nodes"]
        # Sequential connections between non-outcome nodes
        main_chain = [n for n in nodes if n.get("type","normal") not in ("outcome-yes","outcome-no")]
        for j in range(len(main_chain) - 1):
            conns.append({"from": main_chain[j]["id"], "to": main_chain[j+1]["id"],
                          "color": col, "type": "right-to-left"})

        # Outcome splits
        for node in nodes:
            if node.get("type") in ("outcome-yes","outcome-no"):
                src = node.get("connects_from")
                if src:
                    lbl = node.get("label","")
                    conns.append({"from": src, "to": node["id"],
                                  "color": col, "label": lbl, "type": "diagonal-split"})

        # Explicit extra connections (like 2-3 -> 2-5)
        for node in nodes:
            if "connects_from" in node and node.get("type","normal") not in ("outcome-yes","outcome-no"):
                src = node["connects_from"]
                # Only add if not already covered by main chain
                existing = [(c["from"],c["to"]) for c in conns]
                if (src, node["id"]) not in existing:
                    conns.append({"from": src, "to": node["id"],
                                  "color": col, "type": "right-to-left"})

        # Loop-back
        if "loop_back" in blk:
            lb = blk["loop_back"]
            conns.append({"from": lb["from"], "to": lb["to"],
                          "color": colors["loop"], "label": lb.get("label",""), "type": "loop-back"})

    # Floating node connections
    fl = cfg.get("block3_floating", {})
    for src in (fl.get("connects_from") or []):
        lbl = fl.get(f"connect_label_from_{src}", "")
        conns.append({"from": src, "to": fl["id"], "color": colors["orange"],
                      "label": lbl, "type": "top-to-bottom" if src.startswith("2-") else ""})

    return conns


def conn_to_js(c):
    parts = [f"from: '{c['from']}'", f"to: '{c['to']}'", f"color: '{c['color']}'"]
    if c.get("label"):
        parts.append(f"label: '{c['label']}'")
    if c.get("type"):
        parts.append(f"type: '{c['type']}'")
    return "      { " + ", ".join(parts) + " },"


# ── 建立 Block HTML ──────────────────────────────────────────────────────────

# Build the 3 block HTMLs
b1_html = build_block_html("block1")
b2_html = build_block_html("block2")
b3_html = build_block_html("block3")

# Floating node (3-7) — static, build from config
fl = cfg["block3_floating"]
floating_html = f'''              <!-- Mid-level Floating Care Group Takeover Node -->
              <div class="w-full flex justify-end pr-36 -my-10 z-30">
                <div id="node-{fl["id"]}" class="glass-card glow-orange w-56 p-4 rounded-xl cursor-pointer flex flex-col justify-between h-24 border-amber-500/25" onclick="handleNodeClick(event, '{fl["id"]}')">
                  <div class="flex justify-between items-start">
                    <span class="text-[10px] text-orange-700 font-semibold tracking-wider">{fl["step_label"]}</span>
                    <i data-lucide="{fl["icon"]}" class="w-3.5 h-3.5 text-orange-700"></i>
                  </div>
                  <div class="font-bold text-xs text-stone-850 mt-1">{fl["title"]}</div>
                  <div class="text-[9px] text-stone-450 mt-1">{fl["subtitle"]}</div>
                </div>
              </div>'''

# ── Replace canvas section in HTML ──────────────────────────────────────────

CANVAS_PATTERN = re.compile(
    r'(<!-- BLOCK 1:.*?<!-- BLOCK 3: Orange.*?</section>)',
    re.DOTALL
)

new_canvas = (
    "<!-- BLOCK 1: Green Onboarding Section -->\n"
    + b1_html + "\n        \n"
    + "              <!-- BLOCK 2: Blue System Monitoring Section -->\n"
    + b2_html + "\n        \n"
    + floating_html + "\n        \n"
    + "              <!-- BLOCK 3: Orange Regular Pastoring Section -->\n"
    + b3_html
)

new_html, count = CANVAS_PATTERN.subn(new_canvas, html)
if count == 0:
    print("❌ 找不到 canvas 區段，請確認 HTML 結構沒有被手動破壞")
    sys.exit(1)

# ── Replace connections array ────────────────────────────────────────────────

conns = build_connections(["block1","block2","block3"])
conn_lines = "\n".join(conn_to_js(c) for c in conns)
new_connections_block = f"    const connections = [\n{conn_lines}\n    ];"

CONN_PATTERN = re.compile(
    r'const connections = \[.*?\];',
    re.DOTALL
)
new_html, ccount = CONN_PATTERN.subn(new_connections_block, new_html)
if ccount == 0:
    print("❌ 找不到 connections 陣列，請確認 JS 結構沒有被修改")
    sys.exit(1)

# ── Write output ─────────────────────────────────────────────────────────────

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(new_html)

print(f"✅ 完成！成功更新 {HTML_FILE}")
print(f"   • 節點 Block 1: {len([n for n in cfg['block1']['nodes']])} 個")
print(f"   • 節點 Block 2: {len([n for n in cfg['block2']['nodes']])} 個")
print(f"   • 節點 Block 3: {len([n for n in cfg['block3']['nodes']])} 個（+ 1 個浮動節點）")
print(f"   • 自動建立連接線: {len(conns)} 條")
print()
print("📋 連接線清單：")
for c in conns:
    lbl = f" [{c['label']}]" if c.get("label") else ""
    print(f"   {c['from']} → {c['to']}{lbl}")

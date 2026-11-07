# -*- coding: utf-8 -*-
"""简谱自排谱面模板（示例数据：《致爱丽丝》新手完整版 A–B–A–尾声，3 页）。

改数据即可换曲；输出目录可用环境变量 JIANPU_OUT_DIR 指定，默认是本文件旁的 full/。
生成 HTML 后用 Edge 无头截图，再用 crop_white.py 裁白边。
"""
import os

OUT_DIR = os.environ.get(
    "JIANPU_OUT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "full"),
)
os.makedirs(OUT_DIR, exist_ok=True)


def N(d, octv=0, fing='', acc='', dur=8):
    return {'d': d, 'oct': octv, 'fing': fing, 'acc': acc, 'dur': dur}


def R():
    return {'d': '0', 'oct': 0, 'fing': '', 'acc': '', 'dur': 0}


def S():
    return {'d': '-', 'oct': 0, 'fing': '', 'acc': '', 'dur': 0}


def s16(*items):
    """一个八分拍内放两个十六分音符"""
    return list(items)


# ---------- A 段（主题） ----------
E5 = lambda f: N('3', 1, f, dur=16)
DS5 = lambda f: N('2', 1, f, '#', dur=16)
RUN1 = [s16(E5('3'), DS5('2')), s16(E5('3'), DS5('2')), s16(E5('3'), DS5('2'))]
RUN2 = [s16(E5('3'), DS5('2')), s16(E5('3'), N('7', 0, '1', dur=16)),
        s16(N('2', 1, '2', dur=16), N('1', 1, '1', dur=16))]

PICK = [s16(E5('3'), DS5('2')), [R()], [R()]]
M1 = RUN1
M2 = RUN2
M3 = [[N('6', 0, '1')], [S()], [S()]]
M4 = [[N('1', 0, '1')], [N('3', 0, '2')], [N('6', 0, '4')]]
M5 = [[N('7', 0, '5')], [S()], [S()]]
M6 = [[N('3', 0, '1')], [N('5', 0, '2', '#')], [N('7', 0, '4')]]
M7 = [[N('1', 1, '5')], [S()], [S()]]
M8 = RUN1
M9 = RUN2
M10 = [[N('6', 0, '1')], [S()], [S()]]
M11 = [[N('1', 0, '1')], [N('3', 0, '2')], [N('6', 0, '4')]]
M12 = [[N('7', 0, '5')], [S()], [S()]]
M13 = [[N('7', 0, '1')], [N('1', 1, '2')], [N('7', 0, '1')]]
M14 = [[N('6', 0, '1')], [S()], [S()]]

# ---------- B 段（上行模进，接回主题） ----------
M15 = [[N('7', 0, '1')], [N('1', 1, '2')], [N('2', 1, '3')]]
M16 = [[N('3', 1, '1')], [N('4', 1, '2')], [N('3', 1, '1')]]
M17 = [[N('2', 1, '3')], [N('3', 1, '4')], [N('2', 1, '3')]]
M18 = [[N('1', 1, '2')], [N('2', 1, '3')], [N('1', 1, '2')]]
M19 = [[N('7', 0, '1')], [S()], [S()]]

# ---------- A 段再现 + 尾声 ----------
M20 = RUN1
M21 = RUN2
M22 = [[N('6', 0, '1')], [S()], [S()]]
M23 = [[N('7', 0, '1')], [N('1', 1, '2')], [N('7', 0, '1')]]
M24 = [[N('6', 0, '1')], [S()], [S()]]

CHORDS = {0: '', 1: 'Am', 2: 'Am', 3: 'Am', 4: 'Am', 5: 'E', 6: 'E', 7: 'Am',
          8: 'Am', 9: 'Am', 10: 'Am', 11: 'Am', 12: 'E', 13: 'E', 14: 'Am',
          15: 'C', 16: 'C', 17: 'G', 18: 'G', 19: 'Am',
          20: 'Am', 21: 'Am', 22: 'Am', 23: 'E', 24: 'Am'}
LH = {0: '', 1: '6̣', 2: '6̣', 3: '6̣', 4: '6̣', 5: '3̣', 6: '3̣', 7: '6̣',
      8: '6̣', 9: '6̣', 10: '6̣', 11: '6̣', 12: '3̣', 13: '3̣', 14: '6̣',
      15: '1̣', 16: '1̣', 17: '5̣', 18: '5̣', 19: '6̣',
      20: '6̣', 21: '6̣', 22: '6̣', 23: '3̣', 24: '6̣'}


def note_html(n):
    d = n['d']
    if d == '0':
        return '<div class="nw"><div class="fing"></div><div class="glyph rest">0</div></div>'
    if d == '-':
        return '<div class="nw"><div class="fing"></div><div class="glyph dash">—</div></div>'
    acc = '<span class="acc">#</span>' if n['acc'] else ''
    cls = 'glyph'
    if n['dur'] == 16:
        cls += ' u2'
    elif n['dur'] == 8:
        cls += ' u1'
    dot = ''
    if n['oct'] > 0:
        dot = '<span class="dot up">•</span>'
    elif n['oct'] < 0:
        dot = '<span class="dot dn">•</span>'
    return (f'<div class="nw"><div class="fing">{n["fing"]}</div>'
            f'<div class="{cls}">{acc}{d}{dot}</div></div>')


def measure_html(mid, notes, first=False):
    slots = ''.join('<div class="slot">' + ''.join(note_html(x) for x in s) + '</div>'
                    for s in notes)
    chord = CHORDS.get(mid, '')
    lh = LH.get(mid, '')
    label = f'<div class="lab">{chord}<span class="lh">{lh}</span></div>' if (chord or lh) else '<div class="lab"></div>'
    numtag = f'<div class="mnum">{mid if mid else ""}</div>'
    extra = ' first' if first else ''
    return (f'<div class="measure{extra}"><div class="mrow">{slots}</div>'
            f'{label}{numtag}</div>')


CSS = """
* { box-sizing: border-box; margin:0; padding:0; }
html, body { background:#fff; }
.page { width:1240px; background:#fff; padding:56px 52px 44px;
        font-family:"Times New Roman","Noto Serif SC","Songti SC",SimSun,serif; color:#111;
        display:flex; flex-direction:column; }
.head { text-align:center; }
.head h1 { font-size:40px; font-weight:700; letter-spacing:2px; line-height:1.2; }
.head .sub { font-size:18px; color:#c0392b; letter-spacing:2px; margin-top:8px;
             font-family:"Microsoft YaHei",sans-serif; }
.info { display:flex; flex-direction:row; justify-content:space-between; align-items:center;
        margin-top:20px; padding:9px 6px; border-top:2px solid #111; border-bottom:1px solid #ddd;
        font-size:16px; color:#333; font-family:"Microsoft YaHei",sans-serif; }
.sect { display:flex; flex-direction:row; align-items:center; margin:26px 0 2px; }
.sect span { font-size:16px; color:#b8860b; font-family:"Microsoft YaHei",sans-serif;
             letter-spacing:1px; font-weight:bold; }
.sect .line { flex:1 1 auto; height:1px; background:#e2e2e2; margin-left:14px; }
.rowwrap { margin:30px 0 18px; }
.row { display:flex; flex-direction:row; flex-wrap:wrap; align-items:flex-end; }
.measure { display:flex; flex-direction:column; align-items:flex-start; justify-content:flex-end;
           padding:0 20px 0 4px; margin-right:20px; border-right:2px solid #111; }
.measure.first { border-left:2px solid #111; padding-left:12px; }
.mrow { display:flex; flex-direction:row; align-items:flex-end; }
.slot { display:flex; flex-direction:row; margin-right:16px; }
.nw { display:flex; flex-direction:column; align-items:center; width:64px; }
.fing { font-size:17px; color:#c0392b; height:24px; line-height:24px;
        font-family:Arial,sans-serif; }
.glyph { font-size:66px; line-height:74px; position:relative;
         font-family:"Times New Roman",serif; text-align:center; }
.u1 { border-bottom:3px solid #111; }
.u2 { border-bottom:3px solid #111; }
.u2::after { content:""; position:absolute; left:0; right:0; bottom:-8px; height:3px;
             background:#111; }
.dot { position:absolute; font-size:34px; line-height:1; }
.dot.up { top:-16px; left:50%; transform:translateX(-40%); }
.dot.dn { bottom:-14px; left:50%; transform:translateX(-40%); }
.acc { font-size:34px; vertical-align:10px; margin-right:-3px; }
.rest { color:#777; }
.dash { color:#555; }
.lab { display:flex; flex-direction:row; align-items:baseline; margin-top:10px;
       font-family:Arial,"Microsoft YaHei",sans-serif; font-size:16px; color:#555; height:22px; }
.lab .lh { font-size:18px; color:#888; margin-left:9px; font-family:"Times New Roman",serif; }
.mnum { font-size:14px; color:#c4c4c4; font-family:Arial,sans-serif; }
.legend { border-top:1px dashed #ccc; padding-top:16px; margin-top:18px; font-size:17px;
          line-height:2; color:#444; font-family:"Microsoft YaHei",sans-serif; }
.legend b { color:#111; }
.tips { background:#faf7f2; border-left:4px solid #c0392b; padding:14px 18px; margin-top:14px;
        font-size:17px; line-height:2; color:#444; font-family:"Microsoft YaHei",sans-serif; }
.foot { text-align:center; font-size:15px; color:#aaa; margin-top:16px;
        font-family:"Microsoft YaHei",sans-serif; }
"""


def page_html(subtitle, blocks, bottom_html, foot):
    out = []
    for sect_title, rows in blocks:
        out.append(f'<div class="sect"><span>{sect_title}</span><div class="line"></div></div>')
        for row in rows:
            ms = ''.join(measure_html(mid, notes, first=(i == 0))
                         for i, (mid, notes) in enumerate(row))
            out.append(f'<div class="rowwrap"><div class="row">{ms}</div></div>')
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{CSS}</style></head><body><div class="page">
<div class="head"><h1>《致爱丽丝》新手完整版简谱</h1><div class="sub">{subtitle}</div></div>
<div class="info"><span>1 = C　3/8　♩. = 52</span><span>右手主旋律带指法 · 左手一个根音</span><span>A–B–A–尾声</span></div>
{''.join(out)}
{bottom_html}
<div class="foot">{foot}</div>
</div></body></html>"""


legend1 = ('<div class="legend"><b>读谱提示：</b>数字 1–7＝do re mi fa sol la si；'
           '数字<b>上方小点</b>是高八度，<b>下方小点</b>是低八度；数字下一条横线＝八分音符，'
           '两条＝十六分音符；“—”是延音，“0”是休止；<span style="color:#c0392b">数字上方红色小字＝指法</span>；'
           '小节下方是左手（Am 弹低音 la，E 弹低音 mi，C 弹 do，G 弹低音 sol）。</div>')

p1 = page_html('Für Elise · 贝多芬 · 完整版（第 1 页 / 共 3 页）', [
    ('A 段 · 主题第一句（1–7 小节）', [
        [(0, PICK), (1, M1)],
        [(2, M2), (3, M3)],
        [(4, M4), (5, M5)],
        [(6, M6), (7, M7)],
    ]),
], legend1, '第 1 页 / 共 3 页　·　新手完整版')

p2 = page_html('Für Elise · 贝多芬 · 完整版（第 2 页 / 共 3 页）', [
    ('A 段 · 主题第二句（8–14 小节）', [
        [(8, M8), (9, M9)],
        [(10, M10), (11, M11)],
        [(12, M12), (13, M13), (14, M14)],
    ]),
], '<div class="tips"><b>主题段练习要点：</b>① 1–2、8–9 小节是六个十六分音符连跑，'
   '先按 3-2-3-2-3-2 指法单独循环，练到不用看谱；② 4、11 小节的 do–mi–la 上行琶音用 1-2-4 指，'
   '手掌别塌；③ 6 小节的 #sol 是全曲唯一临时升号，注意别弹成 sol；'
   '④ 每个长音后面都要“空够拍”，别急着弹下一句。</div>', '第 2 页 / 共 3 页　·　新手完整版')

p3 = page_html('Für Elise · 贝多芬 · 完整版（第 3 页 / 共 3 页）', [
    ('B 段 · 上行模进（15–19 小节）', [
        [(15, M15), (16, M16), (17, M17)],
        [(18, M18), (19, M19)],
    ]),
    ('A 段再现 + 尾声（20–24 小节）', [
        [(20, M20), (21, M21)],
        [(22, M22), (23, M23), (24, M24)],
    ]),
], '<div class="tips"><b>整曲结构：</b>A 段（主题）→ B 段（上行模进，情绪变亮）→ A 段再现 → 尾声收在 la。<br>'
   '<b>B 段练法：</b>7-1-2 / 3-4-3 / 2-3-2 / 1-2-1 指法逐小节往上爬，左手换成 do、低音 sol 两个音，'
   '整段只用两个和弦，最简单的一段，也是最好听的一段。<br>'
   '<b>省略说明：</b>原曲还有一段 C 段（半音阶和弦段落），是全曲最难的部分，本版为保证新手能弹完而省略，'
   '不影响整曲结构完整。</div>', '第 3 页 / 共 3 页　·　新手完整版')

for name, html in (('page1', p1), ('page2', p2), ('page3', p3)):
    with open(os.path.join(OUT_DIR, name + '.html'), 'w', encoding='utf-8') as f:
        f.write(html)
print('written', OUT_DIR)

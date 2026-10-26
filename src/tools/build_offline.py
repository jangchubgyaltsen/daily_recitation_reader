"""把 app/index.html 做成可以直接发给别人的单个文件：去掉 Google 字体链接（国内打不开会卡住），
把藏文字体（Noto Serif Tibetan，OFL 授权）直接打包进去，中文用系统自带字体。
用法：python3 tools/build_offline.py <输出 html>（先跑 build_app.py）"""
import base64, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(f'{root}/app/index.html', encoding='utf-8').read()
font = base64.b64encode(open(f'{root}/app/fonts/NotoSerifTibetan.woff2', 'rb').read()).decode()
face = ("<style>@font-face{font-family:'Noto Serif Tibetan';font-style:normal;font-weight:400 700;font-display:swap;"
        f"src:url(data:font/woff2;base64,{font}) format('woff2');unicode-range:U+0F00-0FFF,U+200C-200D,U+25CC}}</style>")
t, n = re.subn(r'<link rel="preconnect"[^>]*>\s*<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', face, t)
assert n == 1, '没找到字体链接'
if not t.lstrip().lower().startswith('<!doctype'):
    t = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + t + '</body></html>'
open(sys.argv[1], 'w', encoding='utf-8').write(t)
print('ok', f'{os.path.getsize(sys.argv[1])/1e6:.1f} MB', '外链：', sorted(set(re.findall(r'https?://[\w.-]+', t))))

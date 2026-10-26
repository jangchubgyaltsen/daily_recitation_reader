"""生成 GitHub Pages 上的网页版（iOS 用 Safari 打开后“添加到主屏幕”，之后可离线使用）。
直接从模板和仪轨数据生成（不经过离线版）。音频是单独的文件（a/<哈希>.mp3），没有 16 MB 的限制：
网页先出来，音频在后台下载存到手机上，点到还没下载的会先下载这一个。
藏文字体（Noto Serif Tibetan，OFL）放在 fonts/ 里，不用 Google 字体（国内打不开会卡住）。
用法：python3 tools/build_pages.py <输出目录（daily_recitation_reader 仓库）>"""
import hashlib, json, os, re, shutil, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
subprocess.run([sys.executable, f'{root}/tools/build_app.py', '--pages', out], check=True)
subprocess.run([sys.executable, f'{root}/tools/sync_src.py', out], check=True)  # 源文件一起进仓库，每次发布都有记录
t = open(f'{out}/index.html', encoding='utf-8').read()
audio = json.load(open(f'{out}/audio-files.json'))
# 打开时的上师法相：pages/splash/*.jpg，按内容哈希放进 a/，和音频一样存在手机上
splash = []
for f in sorted(os.listdir(f'{root}/pages/splash')):
    if not f.endswith('.jpg'): continue
    b = open(f'{root}/pages/splash/{f}', 'rb').read()
    n = f'a/{hashlib.sha1(b).hexdigest()[:12]}.jpg'
    open(f'{out}/{n}', 'wb').write(b)
    splash.append(n)
assert t.count('/*SPLASH*/[]') == 1
t = t.replace('/*SPLASH*/[]', json.dumps(splash))
audio += splash
os.makedirs(f'{out}/fonts', exist_ok=True)
shutil.copy(f'{root}/app/fonts/NotoSerifTibetan.woff2', f'{out}/fonts/NotoSerifTibetan.woff2')
face = ("<style>@font-face{font-family:'Noto Serif Tibetan';font-style:normal;font-weight:400 700;font-display:swap;"
        "src:url(fonts/NotoSerifTibetan.woff2) format('woff2');unicode-range:U+0F00-0FFF,U+200C-200D,U+25CC}</style>")
t, n = re.subn(r'<link rel="preconnect"[^>]*>\s*<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', face, t)
assert n == 1, '没找到字体链接'
if not t.lstrip().lower().startswith('<!doctype'):
    t = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + t + '</body></html>'
name = '藏汉课诵'
head = ('<link rel="manifest" href="manifest.webmanifest">'
        '<link rel="apple-touch-icon" href="icon-180.png">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="mobile-web-app-capable" content="yes">'
        f'<meta name="apple-mobile-web-app-title" content="{name}">'
        '<meta name="theme-color" content="#7a1f1f">')
assert t.count('</head>') == 1
t = t.replace('</head>', head + '</head>', 1)
sw_reg = "<script>if('serviceWorker' in navigator)addEventListener('load',()=>navigator.serviceWorker.register('sw.js'))</script>"
assert t.rstrip().endswith('</body></html>')
t = t.rstrip()[:-len('</body></html>')] + sw_reg + '</body></html>'
open(f'{out}/index.html', 'w', encoding='utf-8').write(t)
for f in ['icon-180.png', 'icon-512.png']:
    shutil.copy(f'{root}/pages/{f}', f'{out}/{f}')
json.dump({'name': '藏汉课诵阅读器', 'short_name': name, 'start_url': './', 'scope': './', 'display': 'standalone',
           'background_color': '#f6f3ee', 'theme_color': '#7a1f1f',
           'icons': [{'src': 'icon-180.png', 'sizes': '180x180', 'type': 'image/png'},
                     {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]},
          open(f'{out}/manifest.webmanifest', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# 两个缓存：网页本身（每次更新换名字，整页重新下）和音频（名字固定；文件名是内容哈希，
# 已经下过的不再下，只补新的、删掉不再用的）。安装时只等网页；音频在后台慢慢补。
ver = hashlib.sha1((t + json.dumps(audio)).encode()).hexdigest()[:10]
open(f'{out}/sw.js', 'w').write(f"""const C='recite-{ver}',A='recite-audio',FILES=['./','index.html','manifest.webmanifest','icon-180.png','icon-512.png','fonts/NotoSerifTibetan.woff2'];
const AUDIO={json.dumps(audio)};
const base=f=>f.split('/').pop();
async function fillAudio(){{const c=await caches.open(A),keys=await c.keys(),have=new Set(keys.map(r=>base(new URL(r.url).pathname))),want=new Set(AUDIO.map(base));
  for(const r of keys)if(!want.has(base(new URL(r.url).pathname)))await c.delete(r);
  for(const f of AUDIO)if(!have.has(base(f)))try{{await c.add(f)}}catch(e){{}}}}
self.addEventListener('install',e=>{{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(FILES)))}});
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C&&k!==A).map(k=>caches.delete(k)))).then(()=>self.clients.claim()).then(()=>{{fillAudio()}})));
self.addEventListener('fetch',e=>{{
  if(e.request.method!=='GET'||new URL(e.request.url).origin!==location.origin)return;
  if(new URL(e.request.url).pathname.includes('/a/'))return e.respondWith(caches.open(A).then(c=>c.match(e.request,{{ignoreSearch:true}}).then(r=>r||fetch(e.request).then(res=>{{if(res.ok)c.put(e.request,res.clone());return res}}))));
  e.respondWith(caches.match(e.request,{{ignoreSearch:true}}).then(r=>r||(e.request.mode==='navigate'?caches.match('index.html'):null)).then(r=>r||fetch(e.request)));
}});
""")
os.remove(f'{out}/audio-files.json')
mb = sum(os.path.getsize(f'{out}/{f}') for f in audio) / 1e6
print('ok', out, f'网页 {os.path.getsize(out + "/index.html")/1e6:.1f} MB', f'音频 {len(audio)} 个 {mb:.1f} MB', '版本', ver)

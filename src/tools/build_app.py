"""把 rituals/*.json 嵌进阅读器，生成 app/index.html。先运行 check.py。
python3 tools/build_app.py --pages <目录>：给 GitHub Pages 用，音频不打包进网页，
每个文件按内容哈希另存成 <目录>/a/<哈希>.mp3（原音质），网页用到时再下载。"""
import json, os, hashlib, shutil
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
order = ['eight-auspicious', 'multiplying-mantra', 'wangdu-prayer', 'ngondro', 'offering', 'seven-branch', 'bodhisattva-vow', 'seven-line-prayer', 'siddhi-prayer', 'shakyamuni', 'protector-offering', 'guru-yoga', 'manjushri-praise', 'longchenpa-prayer', 'mipham-prayer-1', 'mipham-prayer-2', 'jigme-phuntsok-prayer', 'manjushri-mantra', 'manjushri-wisdom', 'request-dharma', 'dedication-verse', 'samantabhadra-aspiration', 'truth-words', 'aspiration-mantra', 'wishfulfilling-guru-prayer', 'menkhyo-longevity', 'auspicious-verse', 'guru-rinpoche-mantra', 'aspiration-ocean', 'manjushri-dzogchen-aspiration', 'teaching-endure-aspiration', 'swift-fulfillment-prayer', 'remainder-offering', 'inexpressible-confession', 'tsok-short', 'kangwa-short', 'seven-line-guru-yoga', 'seven-vajra-tsok', 'refuge-bodhicitta-verse', 'four-immeasurables', 'guru-khyen', 'guru-rinpoche-supplication', 'lineage-prayer', 'vajrasattva-100', 'vajrasattva-mantra', 'shakyamuni-mantra', 'mandala-mantra', 'offering-cloud-mantra', 'akashagarbha-mantra', 'refuge-four', 'refuge-bodhicitta-mipham', 'mipham-auspicious-prayer', 'barche-lamsel-short', 'amitayus-prayer', 'medicine-buddha-prayer', 'chenrezig-prayer', 'tara-prayer', 'tara-eight-fears-prayer', 'marici-prayer', 'marici-praise', 'dhvajagra-praise', 'tharpa-sutra-short', 'thubten-chophel-aspiration', 'jigme-phuntsok-aspiration', 'shakyamuni-name', 'amitabha-name', 'medicine-buddha-name', 'ksitigarbha-name', 'chenrezig-name', 'medicine-buddha-dharani', 'medicine-buddha-mantra-short', 'longevity-dharani', 'amitayus-mantra-short', 'achala-mantra', 'vairocana-mantra', 'amitabha-dharani', 'amitabha-mantra', 'peaceful-wrathful-mantra', 'jigme-phuntsok-mantra', 'wrathful-guru-mantra', 'vajrakilaya-mantra', 'chenrezig-mantra', 'hayagriva-mantra', 'hayagriva-dharani', 'yamantaka-mantra-1', 'yamantaka-mantra-2', 'vajrapani-mantra', 'three-protectors-mantra', 'prajnaparamita-mantra', 'tara-mantra', 'white-tara-mantra', 'marici-mantra', 'parnashavari-mantra', 'sitatapatra-mantra', 'simhamukha-mantra', 'ushnishavijaya-mantra', 'vasudhara-mantra', 'alphabet-mantra', 'dependent-origination-mantra', 'liberation-mantra', 'urna-light-mantra', 'vajra-armor-mantra', 'epidemic-mantra', 'ucchusma-mantra', 'lion-roar-dharani', 'vajra-vidarana-dharani', 'kagye-mantra', 'garuda-mantra', 'mahakala-mantra', 'thirteen-chakra-mantra', 'pure-discipline-dharani', 'offering-purification-dharani', 'prostration-multiplying-mantra', 'circumambulation-mantra', 'akshobhya-mantra', 'great-compassion-dharani', 'meal-offering']
data = [json.load(open(f'{root}/rituals/{n}.json', encoding='utf-8')) for n in order]
data = [r for r in data if r['meta'].get('restriction') == 'public']  # 需灌顶的内容不进公开版本
import sys; sys.path.insert(0, f'{root}/tools'); import lexicon
lex = lexicon.load()
used = {w: 'lexicon/bo/' + lex[w]['file'] for r in data for w in lexicon.ritual_words(r) if w in lex}
# 录音和词库发音直接打包进网页（data: URL），手机上不用另外取文件
import base64
files = sorted(set(used.values()) | {r['meta'][k] for r in data for k in r['meta'] if k.startswith('audio.') and '.' not in k[6:] and os.path.exists(f"{root}/{r['meta'][k]}")})
# 词库发音只在释义卡里点读，压成 24 kbps 存在本机 ~/.cache/bagui-bo-small/（缓存，不改原文件；不放在共享文件夹里，那里曾被同步回旧文件），整页才放得进 16 MB 的上限
import subprocess
def small(f):
    if not f.startswith('lexicon/bo/'): return f'{root}/{f}'
    out = os.path.expanduser(f"~/.cache/bagui-bo-small/{os.path.basename(f)}")
    # 词库换过发音就重压；缓存文件不像 24 kbps（比原文件一半还大，曾被别的构建覆盖成原码率）也重压
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(f'{root}/{f}') or os.path.getsize(out) > os.path.getsize(f'{root}/{f}') / 2:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{root}/{f}', '-map', '0:a', '-map_metadata', '-1', '-id3v2_version', '0', '-write_xing', '0', '-ac', '1', '-b:a', '24k', out], check=True)
    return out
pages = sys.argv[sys.argv.index('--pages') + 1] if '--pages' in sys.argv else None
if pages:
    # 文件名用内容哈希：内容变了名字就变，手机上缓存的旧音频不会被误用；没变的不用重新下载
    os.makedirs(f'{pages}/a', exist_ok=True)
    moved = {}
    for f in files:
        b = open(f'{root}/{f}', 'rb').read()
        moved[f] = f'a/{hashlib.sha1(b).hexdigest()[:16]}.mp3'
        if not os.path.exists(f'{pages}/{moved[f]}'): open(f'{pages}/{moved[f]}', 'wb').write(b)
    for old_f in os.listdir(f'{pages}/a'):
        if f'a/{old_f}' not in moved.values(): os.remove(f'{pages}/a/{old_f}')
    used = {w: moved[f] for w, f in used.items()}
    for r in data:
        for k in list(r['meta']):
            if isinstance(r['meta'][k], str) and r['meta'][k] in moved: r['meta'][k] = moved[r['meta'][k]]
    audio, out = {}, f'{pages}/index.html'
    open(f'{pages}/audio-files.json', 'w').write(json.dumps(sorted(moved.values())))
else:
    # claude.ai 预览版：音频不放进网页，分成几个 a/p<n>.js 包（每个不到 12 MB），和网页一起发布；
    # 包里的脚本把音频加进 window.__AUD，网页里的 AUDIO 就是这个对象，所以不用改模板
    out = f'{root}/app/index.html'
    os.makedirs(f'{root}/app/a', exist_ok=True)
    for old_f in os.listdir(f'{root}/app/a'): os.remove(f'{root}/app/a/{old_f}')
    packs, cur = [], []
    for f in files:
        u = 'data:audio/mpeg;base64,' + base64.b64encode(open(small(f), 'rb').read()).decode()
        if cur and sum(len(x) for x in cur) + len(u) > 12e6: packs.append(cur); cur = []
        cur.append(f'w[{json.dumps(f)}]={json.dumps(u)};')
    if cur: packs.append(cur)
    for i, p in enumerate(packs):
        open(f'{root}/app/a/p{i}.js', 'w').write('(function(w){' + ''.join(p) + '})(window.__AUD=window.__AUD||{});')
    audio = None
t = open(f'{root}/app/template.html', encoding='utf-8').read()
# 音译用楷体（w）：霞鹜文楷（OFL，原文件在 app/fonts/src/）按仪轨里出现的音译字裁出子集，内嵌进网页。
# 有新字才重裁；这台机器没装 fontTools（pip install fonttools brotli）就先用已有的子集，新字退回系统楷体
kai, stamp = f'{root}/app/fonts/kai-ph.woff2', f'{root}/app/fonts/kai-ph.chars'
need = {c for r in data for s in r['sections'] for l in s['lines'] for c in l.get('zh_ph', '') + ''.join(y.get('zh_ph', '') for y in l.get('syllables', [])) if not c.isspace()}
need |= {c for c in '·（）' }
if not os.path.exists(stamp) or need - set(open(stamp, encoding='utf-8').read()):
    try:
        from fontTools import subset
        o = subset.Options(); o.flavor = 'woff2'
        from fontTools.ttLib import newTable; import struct
        fnt = subset.load_font(f'{root}/app/fonts/src/LXGWWenKai-Regular.ttf', o, lazy=True)
        # 这个字体的 format 4 cmap 子表 fontTools 读不了，只留 format 12（偏移按删掉的表头记录前移）
        d = fnt.reader['cmap']; n = struct.unpack('>H', d[2:4])[0]
        recs = [struct.unpack('>HHI', d[4 + 8 * i:12 + 8 * i]) for i in range(n)]
        keep = [r for r in recs if struct.unpack('>H', d[r[2]:r[2] + 2])[0] == 12]; sh = 8 * (n - len(keep))
        cm = newTable('cmap'); cm.decompile(struct.pack('>HH', 0, len(keep)) + b''.join(struct.pack('>HHI', a, b, c - sh) for a, b, c in keep) + d[4 + 8 * n:], fnt); fnt['cmap'] = cm
        sb = subset.Subsetter(o); sb.populate(text=''.join(sorted(need))); sb.subset(fnt); subset.save_font(fnt, kai, o)
        open(stamp, 'w', encoding='utf-8').write(''.join(sorted(need)))
    except ImportError: print('提示：没装 fontTools，音译楷体用旧子集')
# w 2026-10-27 改用文鼎简中楷（gkai00mp，Arphic Public License，原文件在 app/fonts/src/）。
# 它缺的少数字（如吽）仍用上面的霞鹜文楷子集补：两个 @font-face 同名，用 unicode-range 分开。
gk, gstamp = f'{root}/app/fonts/gkai-ph.woff2', f'{root}/app/fonts/gkai-ph.chars'
if not os.path.exists(gstamp) or need - set(open(gstamp, encoding='utf-8').read()):
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
        o = subset.Options(); o.flavor = 'woff2'
        g = subset.load_font(f'{root}/app/fonts/src/gkai00mp.ttf', o)
        has = ''.join(sorted(c for c in need if ord(c) in g.getBestCmap()))
        sb = subset.Subsetter(o); sb.populate(text=has); sb.subset(g); subset.save_font(g, gk, o)
        open(gstamp, 'w', encoding='utf-8').write(''.join(sorted(need)))
    except ImportError: print('提示：没装 fontTools，音译楷体用旧子集')
def urange(cs): return ','.join('U+%X' % ord(c) for c in sorted(cs))
kai_css = ''
if os.path.exists(gk):
    from fontTools.ttLib import TTFont
    gch = {chr(u) for u in TTFont(gk).getBestCmap()}
    kai_css += "@font-face{font-family:'PhKai';font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}" % (base64.b64encode(open(gk, 'rb').read()).decode(), urange(gch))
    rest = need - gch
else: rest = None
if os.path.exists(kai):
    kai_css += "@font-face{font-family:'PhKai';font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2')%s}" % (base64.b64encode(open(kai, 'rb').read()).decode(), ';unicode-range:' + urange(rest) if rest else '')
t = t.replace('/*DATA*/', json.dumps(data, ensure_ascii=False)).replace('/*KAIFONT*/', kai_css).replace('/*LEX*/null', json.dumps(used, ensure_ascii=False))
if audio is None:
    assert t.count('/*AUDIO*/null') == 1
    t = t.replace('/*AUDIO*/null', '(window.__AUD=window.__AUD||{})')
    tags = ''.join(f'<script src="a/p{i}.js"></script>' for i in range(len(packs)))
    i = t.index('<script')  # 放在网页自己的脚本前面：启动时载入的录音要已经在 AUDIO 里
    t = t[:i] + tags + t[i:]
else:
    t = t.replace('/*AUDIO*/null', json.dumps(audio))
open(out, 'w', encoding='utf-8').write(t)
print('ok', len(data), '词库发音', len(used), '打包音频' if not pages else '单独音频文件', len(files), f'{os.path.getsize(out)/1e6:.1f} MB', '' if pages else f'音频包 {len(packs)} 个')
if pages: sys.exit()
open(f'{root}/app/lexicon-files.txt', 'w').write('\n'.join(sorted(set(used.values()))))  # 发布时要一起带上的文件

"""把 rituals/*.json 嵌进阅读器，生成 app/index.html。先运行 check.py。
python3 tools/build_app.py --pages <目录>：给 GitHub Pages 用，音频不打包进网页，
每个文件按内容哈希另存成 <目录>/a/<哈希>.mp3（原音质），网页用到时再下载。"""
import json, os, hashlib, shutil
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
order = ['eight-auspicious', 'multiplying-mantra', 'wangdu-prayer', 'ngondro', 'offering', 'seven-branch']
data = [json.load(open(f'{root}/rituals/{n}.json', encoding='utf-8')) for n in order]
data = [r for r in data if r['meta'].get('restriction') == 'public']  # 需灌顶的内容不进公开版本
import sys; sys.path.insert(0, f'{root}/tools'); import lexicon
lex = lexicon.load()
used = {w: 'lexicon/bo/' + lex[w]['file'] for r in data for w in lexicon.ritual_words(r) if w in lex}
# 录音和词库发音直接打包进网页（data: URL），手机上不用另外取文件
import base64
files = sorted(set(used.values()) | {r['meta'][k] for r in data for k in r['meta'] if k.startswith('audio.') and '.' not in k[6:] and os.path.exists(f"{root}/{r['meta'][k]}")})
# 词库发音只在释义卡里点读，压成 32 kbps 存在 lexicon/bo-32k/（缓存，不改原文件），整页才放得进 16 MB 的上限
import subprocess
def small(f):
    if not f.startswith('lexicon/bo/'): return f'{root}/{f}'
    out = f"{root}/lexicon/bo-32k/{os.path.basename(f)}"
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(f'{root}/{f}'):  # 词库换过发音就重压
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{root}/{f}', '-ac', '1', '-b:a', '32k', out], check=True)
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
    audio = {f: 'data:audio/mpeg;base64,' + base64.b64encode(open(small(f), 'rb').read()).decode() for f in files}
    out = f'{root}/app/index.html'
t = open(f'{root}/app/template.html', encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('/*DATA*/', json.dumps(data, ensure_ascii=False)).replace('/*LEX*/null', json.dumps(used, ensure_ascii=False)).replace('/*AUDIO*/null', json.dumps(audio)))
print('ok', len(data), '词库发音', len(used), '打包音频' if not pages else '单独音频文件', len(files), f'{os.path.getsize(out)/1e6:.1f} MB')
if pages: sys.exit()
open(f'{root}/app/lexicon-files.txt', 'w').write('\n'.join(sorted(set(used.values()))))  # 发布时要一起带上的文件

"""生成「挑发音」页面：每个词的 5 个候选发音打包进一页，w 点着听、选一个。
用法：python3 tools/build_picker.py <候选目录（含 manifest.tsv）> <输出 html> [第几份/共几份，如 1/2]
一页最多 16 MB，词多的时候按出现先后分成几页（每页各有自己的数据库）。
选择结果存在页面的数据库里（picks/<词id>），之后用 lexicon.py 按选择导入。"""
import base64, csv, html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lexicon as L
src, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(f'{src}/manifest.tsv', encoding='utf-8'), delimiter='\t'))
rows = [r for r in rows if os.path.exists(f"{src}/{r['file']}")]  # 没取回的（试过不能用的）版本不放进页面
# w 2026-10-25：只给有区别的几种（甲、乙、连读、前连、垫音），相似的不放
SHOW = set('abfgpqtuvw')
rows = [r for r in rows if r['variant'] in SHOW]
rows = [r for r in rows if not L.is_seed(r['text'])]  # 种子字等真人录音，不挑 AI 版
# 每个词第一次出现在哪一句，方便对照
where, first = {}, {}
for r in L.public_rituals():
    for sec in r['sections']:
        for ln in sec['lines']:
            for wd in ln.get('beat_groups') or ln.get('words') or []:
                w = L.key('་'.join(ln['syllables'][i]['bo'] for i in wd['syl']))
                where.setdefault(w, []).append(f"{r['meta'].get('title.zh','')} 第{ln['id']}句"); first.setdefault(w, len(first) + 10)
    for wd in r['meta'].get('title_words', []):
        w = L.key('་'.join(r['meta']['title_syllables'][i]['bo'] for i in wd['syl']))
        where.setdefault(w, []).insert(0, f"{r['meta'].get('title.zh','')} 标题"); first[w] = min(first.get(w, 1e9), len(first) - 1e6)
# 音译都来自书里每个音节的 zh_ph / 每个词的 en_ph；标题没有音译，按正文里同一音节的读法拼
ph, sylzh = {}, {}
for r in L.public_rituals():
    for sec in r['sections']:
        for ln in sec['lines']:
            syl = ln['syllables']
            for s_ in syl:
                if s_.get('zh_ph'): sylzh.setdefault(L.key(s_['bo']), s_['zh_ph'])
            for wd in ln.get('beat_groups') or ln.get('words') or []:
                w = L.key('་'.join(syl[i]['bo'] for i in wd['syl']))
                zh = ''.join(syl[i].get('zh_ph', '') for i in wd['syl'])
                ew = [] if 'en_words' not in ln else sorted({syl[i]['en_word'] for i in wd['syl'] if syl[i].get('en_word') is not None})
                en = ' '.join(ln['en_words'][i] for i in ew)
                ph.setdefault(w, {'zh': zh, 'en': en, 'mean': wd.get('zh', '')})
    m = r['meta']
    for wd in m.get('title_words', []):
        w = L.key('་'.join(m['title_syllables'][i]['bo'] for i in wd['syl']))
        if w not in ph:
            parts = [sylzh.get(L.key(m['title_syllables'][i]['bo'])) for i in wd['syl']]
            ph[w] = {'zh': ''.join(parts) if all(parts) else '', 'en': '', 'mean': wd.get('zh', ''), 'pieced': True}
words, audio = {}, {}
for row in rows:
    w = words.setdefault(row['id'], {'id': row['id'], 'text': row['text'], 'v': []})
    w['v'].append(row['variant'])
    audio[f"{row['id']}-{row['variant']}"] = 'data:audio/mpeg;base64,' + base64.b64encode(open(f"{src}/{row['file']}", 'rb').read()).decode()
order = list(words.values())
for w in order:
    w['where'] = where.get(L.key(w['text']), [])[:3]
    w['ph'] = ph.get(L.key(w['text']), {})
order.sort(key=lambda w: first.get(L.key(w['text']), 1e9))  # 按在仪轨里出现的先后排
if len(sys.argv) > 3:
    i, n = map(int, sys.argv[3].split('/'))
    # 按音频大小平均分，不按词数（长句子的音频大）
    sz = [sum(len(a) for k, a in audio.items() if k.rsplit('-', 1)[0] == w['id']) for w in order]
    tot, acc, part = sum(sz), 0, []
    for w, b in zip(order, sz):
        if min(n, 1 + int(acc * n / tot)) == i: part.append(w)
        acc += b
    order = part
    keep = {w['id'] for w in order}
    audio = {k: a for k, a in audio.items() if k.rsplit('-', 1)[0] in keep}
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'picker_template.html'), encoding='utf-8').read()
if len(sys.argv) > 3: t = t.replace('挑选词发音', f'开显解脱道 挑选词发音（{sys.argv[3]}）')
t = t.replace('/*WORDS*/null', json.dumps(order, ensure_ascii=False)).replace('/*AUDIO*/null', json.dumps(audio))
open(out, 'w', encoding='utf-8').write(t)
print('ok', len(order), '词', len(audio), '段', f'{os.path.getsize(out)/1e6:.1f} MB')

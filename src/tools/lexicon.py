"""藏文发音词库（MMS-TTS 生成的纯发音，每个词只存一次）。

词库在 lexicon/bo/：index.tsv 记录 词 → 文件，mp3 文件名由词算出，不同仪轨里的同一个词共用一个文件。

  python3 tools/lexicon.py missing        列出所有公开仪轨里词库还没有的词 → lexicon/bo/missing.tsv
  python3 tools/lexicon.py import <目录>   导入 MMS-TTS 生成结果（目录里要有 manifest.tsv：id file … text）
                                          已有的词不覆盖，加 --replace 才覆盖
  python3 tools/lexicon.py picks <候选目录> <picks 目录>
                                          按挑选页的选择（picks/<词id>.json 里的 v）把选中的候选版本换进词库
"""
import csv, glob, hashlib, json, os, shutil, sys, unicodedata
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEX = f'{root}/lexicon/bo'
INDEX = f'{LEX}/index.tsv'
COLS = ['word', 'file', 'seconds', 'source', 'note']

# 挑选页里候选版本的做法（都在 w 电脑上用 mms-tts-adx 生成，末尾补 ་）
VARIANTS = {'a': '单独念 语速0.8 seed0', 'b': '单独念 seed1', 'c': '单独念 seed2', 'd': '单独念 低噪声 seed0', 'e': '单独念 低噪声 seed1',
            'f': '整句念后切出（连读）', 'g': '和前一个词连念（前连）', 'h': '单独念 语速0.65 seed0', 'i': '单独念 语速0.65 seed1',
            'j': '单独念 语速0.65 seed2', 'k': '单独念 语速0.55 seed0', 'l': '单独念 语速0.55 seed1', 'm': '单独念 语速0.65 低噪声',
            'n': '前连 语速0.65', 'o': '前连 语速0.55', 'p': '前面垫 ཨ་ 语速0.65', 'q': '前面垫 ཨ་ 语速0.55',
            't': '前面垫 ཐབ་ 语速0.65', 'u': '前面垫 ཐབ་ 语速0.55', 'v': '前面垫 དག་ 从 ས 切 语速0.65', 'w': '前面垫 དག་ 从 ས 切 语速0.55'}

# 种子字先不放发音（不用 AI 生成），等以后统一用真人录音处理（w 2026-10-26）
SEED = {'ཨོཾ', 'ཨཱཿ', 'ཧཱུྃ', 'ཧྲཱིཿ', 'ཧཱུཾ', 'ཧཱུྂ', 'ཧོཿ'}

# 梵文叠字模型读不全（པདྨ 只念出一半，ཌ 直接丢掉），合成时按读音改写，词库里仍存原文
SPELL = {'པདྨ': 'པད་མ', 'བཛྲ': 'བན་ཛ', 'ཌཱ': 'དཱ', 'མཱནྟ': 'མཱན་ཏ'}

def tts_text(text):
    for a, b in SPELL.items(): text = text.replace(a, b)
    return text

def is_seed(word):
    return key(word) in SEED

def key(word):
    """词的标准写法：NFC，去掉首尾的音节点和句号。"""
    return unicodedata.normalize('NFC', word).strip().strip('་།༎ ')

def fname(word):
    return hashlib.sha1(key(word).encode()).hexdigest()[:12] + '.mp3'

def load():
    if not os.path.exists(INDEX): return {}
    with open(INDEX, encoding='utf-8') as f:
        return {r['word']: r for r in csv.DictReader((l for l in f if not l.startswith('#')), delimiter='\t')}

def save(lex):
    with open(INDEX, 'w', encoding='utf-8', newline='') as f:
        f.write('# 藏文发音词库。note 一栏写已知问题，例如「缺尾音」。改这一栏不需要改代码。\n')
        w = csv.DictWriter(f, COLS, delimiter='\t', extrasaction='ignore'); w.writeheader()
        for k in sorted(lex): w.writerow(lex[k])

def ritual_words(r):
    """一个仪轨里所有可点的词：标题的词 + 每句按律分的节。"""
    m = r['meta']; out = []
    for wd in m.get('title_words', []):
        out.append(key('་'.join(m['title_syllables'][i]['bo'] for i in wd['syl'])))
    for sec in r['sections']:
        for ln in sec['lines']:
            for wd in ln.get('beat_groups') or ln.get('words') or []:
                out.append(key('་'.join(ln['syllables'][i]['bo'] for i in wd['syl'])))
    return out

def public_rituals():
    for p in sorted(glob.glob(f'{root}/rituals/*.json')):
        r = json.load(open(p, encoding='utf-8'))
        if r['meta'].get('restriction') == 'public': yield r

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    lex = load()
    if cmd == 'missing':
        miss = []
        for r in public_rituals():
            for w in ritual_words(r):
                if w and not is_seed(w) and w not in lex and w not in miss: miss.append(w)
        with open(f'{LEX}/missing.tsv', 'w', encoding='utf-8') as f:
            f.write('id\ttext\n'); f.writelines(f'{i}\t{w}\n' for i, w in enumerate(miss))
        print(f'词库已有 {len(lex)} 个词，缺 {len(miss)} 个 → lexicon/bo/missing.tsv')
    elif cmd == 'import':
        src = sys.argv[2]; replace = '--replace' in sys.argv; n = 0
        with open(f'{src}/manifest.tsv', encoding='utf-8') as f:
            for row in csv.DictReader(f, delimiter='\t'):
                w = key(row['text'])
                if not w or is_seed(w) or (w in lex and not replace): continue
                shutil.copy(f"{src}/{row['file']}", f'{LEX}/{fname(w)}')
                lex[w] = {'word': w, 'file': fname(w), 'seconds': row.get('duration_seconds', ''),
                          'source': 'mms-tts-bod', 'note': (lex.get(w) or {}).get('note', '')}
                n += 1
        save(lex); print(f'导入 {n} 个，词库共 {len(lex)} 个')
    elif cmd == 'picks':
        src, pdir = sys.argv[2], sys.argv[3]; n = 0
        rows = {(r['id'], r['variant']): r for r in csv.DictReader(open(f'{src}/manifest.tsv', encoding='utf-8'), delimiter='\t')}
        for pf in sorted(glob.glob(f'{pdir}/*.json')):
            pid = os.path.basename(pf)[:-5]; v = json.load(open(pf, encoding='utf-8')).get('v')
            row = rows.get((pid, v))
            if not row: print('跳过', pid, v); continue
            w = key(row['text'])
            if is_seed(w): print('种子字先不放', w); continue
            shutil.copy(f"{src}/{row['file']}", f'{LEX}/{fname(w)}')
            lex[w] = {'word': w, 'file': fname(w), 'seconds': row.get('duration_seconds', ''),
                      'source': f'mms-tts-adx（安多），w 挑选的候选 {v}：{VARIANTS.get(v, v)}', 'note': ''}
            n += 1
        save(lex); print(f'按挑选换了 {n} 个，词库共 {len(lex)} 个')
    else:
        print(__doc__)

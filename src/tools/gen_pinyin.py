"""生成搜索用的同音字表（w 2026-11-07：同音字都能搜到）。
常用字（GB2312 一级 3755 字）加上仪轨里出现的所有汉字，按拼音分组：不分声调，zh/z、ch/c、sh/s、
in/ing、en/eng 也算一样（咒语音译常这样混用）。每组第一个字是代表字，搜索时都换成它。
另外补几组读音不同、但咒语音译里常互换的字（咪/美、舍/啥 等）。
用法：pip install pypinyin；python3 src/tools/gen_pinyin.py <仓库目录>
会把模板和网页里 /*PY*/"…" 那一行换成新表（两个文件都改）。"""
import glob, json, os, re, sys
from pypinyin import lazy_pinyin
repo = sys.argv[1] if len(sys.argv) > 1 else '.'
chars = set(bytes([a, b]).decode('gb2312') for a in range(0xB0, 0xD8) for b in range(0xA1, 0xFF) if not (a == 0xD7 and b > 0xF9))
for f in glob.glob(f'{repo}/src/rituals/*.json'):
    chars |= {c for c in open(f, encoding='utf-8').read() if '一' <= c <= '鿿'}
def key(c):
    p = lazy_pinyin(c)[0]
    if not p.isalpha(): return None
    p = re.sub(r'^([zcs])h', r'\1', p)
    return re.sub(r'(in|en)g$', r'\1', p)
# 读音不同但音译里常互换的字：并进同一组（代表字用前一个字所在的组）
EXTRA = ['尼呢', '咪美', '舍啥', '嗡唵', '巴贝呗', '萨娑']
groups = {}
for c in sorted(chars, key=lambda c: (c.encode('gb18030'))):
    k = key(c)
    if k: groups.setdefault(k, []).append(c)
canon = {c: k for k, cs in groups.items() for c in cs}
for g in EXTRA:
    ks = [canon.get(c) or key(c) for c in g]
    tgt = ks[0]
    for c, k in zip(g, ks):
        if k != tgt:
            if c not in groups.setdefault(tgt, []): groups[tgt].append(c)
            if k in groups and c in groups[k]: groups[k].remove(c)
s = '|'.join(''.join(cs) for k, cs in sorted(groups.items()) if len(cs) > 1)
line = '/*PY*/' + json.dumps(s, ensure_ascii=False)
for f in [f'{repo}/src/app/template.html', f'{repo}/index.html']:
    t = open(f, encoding='utf-8').read()
    t2, n = re.subn(r'/\*PY\*/"[^"]*"', lambda m: line, t)
    assert n == 1, f
    open(f, 'w', encoding='utf-8').write(t2)
print(len(chars), '字', s.count('|') + 1, '组', len(s.encode()) // 1024, 'KB')

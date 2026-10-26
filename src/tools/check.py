"""校对检查：读取 rituals/*.txt，检查音节对齐和逐词对应，并输出 JSON。
用法：python3 tools/check.py rituals/eight-auspicious.txt
"""
import json, re, sys

def parse(path):
    r = {'meta': {}, 'sections': []}
    sec = line = None
    for raw in open(path, encoding='utf-8'):
        s = raw.strip()
        if not s or s.startswith('#'):
            continue
        if s.startswith('== '):
            sec = {'id': s[3:].strip(), 'lines': []}
            r['sections'].append(sec); line = None; continue
        if s.startswith('-- '):
            line = {'id': s[3:].strip()}
            sec['lines'].append(line); continue
        key, _, val = s.partition(':')
        key, val = key.strip(), val.strip()
        target = line if line is not None else sec if sec is not None else r['meta']
        key = key.lstrip('@')
        if key in target:  # 同一键重复出现（如多条 note）就变成列表
            target[key] = target[key] if isinstance(target[key], list) else [target[key]]
            target[key].append(val)
        else:
            target[key] = val
    return r

def tib_syllables(bo):
    bo = re.sub(r'[།༄༅༔\s]+', '་', bo)
    return [x for x in bo.split('་') if x]

def zh_syllables(ph):
    return re.findall(r'\{[^}]*\}|[一-鿿]|[A-Z][a-z]*', re.sub(r'\d', '', ph))

def en_words(ph):
    """每个拉丁词按元音组估算音节数；{} 括起来算一个音节。"""
    out = []
    for w in re.findall(r"\{[^}]*\}|[^\s,!—]+", ph):
        n = 1 if w.startswith('{') else max(1, len(re.findall(r'[aeiouéüöāīū]+', w.lower())))
        out.append((w.strip('{}'), n))
    return out

def parse_gloss(gloss, ts):
    words, i = [], 0
    for item in gloss.split(';'):
        parts = [p.strip() for p in item.split('=')]
        wsyl = tib_syllables(parts[0])
        if ts[i:i + len(wsyl)] != wsyl:
            return None, f"逐词 “{parts[0]}” 和藏文第{i+1}个音节起对不上"
        words.append({'syl': list(range(i, i + len(wsyl))), 'zh': parts[1] if len(parts) > 1 else '', 'en': parts[2] if len(parts) > 2 else ''})
        i += len(wsyl)
    if i != len(ts):
        return None, f"逐词只覆盖了 {i}/{len(ts)} 个音节"
    return words, None

def find(ts, word, nth=1):
    for i in range(len(ts) - len(word) + 1):
        if ts[i:i + len(word)] == word:
            nth -= 1
            if nth == 0: return list(range(i, i + len(word)))
    return None

def parse_align(text, ts, zh):
    segs = []
    for item in text.split(';'):
        z, _, bo = item.partition('=')
        z, bo = z.strip(), bo.strip()
        nth = 1
        if '@' in bo: bo, n = bo.split('@'); nth = int(n)
        syl = find(ts, tib_syllables(bo), nth) if bo else []
        if syl is None: return None, f"“{bo}”在藏文里找不到"
        segs.append({'t': z, 'syl': syl})
    if ''.join(s['t'] for s in segs) != re.sub(r'\s', '', zh):
        return None, "拼起来和汉文整句不一致"
    return segs, None

def check(r):
    errs = []
    m = r['meta']
    if m.get('title.gloss'):
        ts = tib_syllables(m.get('title.bo', ''))
        m['title_syllables'] = [{'bo': t} for t in ts]
        words, err = parse_gloss(m['title.gloss'], ts)
        if err: errs.append(f"标题：{err}")
        else: m['title_words'] = words
    kind = r['meta'].get('kind')
    for sec in r['sections']:
        for ln in sec['lines']:
            where = f"{sec['id']} 第{ln['id']}句"
            ts = tib_syllables(ln.get('bo', ''))
            ln['syllables'] = [{'bo': t} for t in ts]
            if kind == 'mantra' or ln.get('kind') == 'mantra':
                continue
            zs = zh_syllables(ln.get('zh_ph', ''))
            if len(zs) != len(ts):
                errs.append(f"{where}：藏文 {len(ts)} 个音节，汉文音译 {len(zs)} 个")
            else:
                for s, z in zip(ln['syllables'], zs): s['zh_ph'] = z.strip('{}')
            ew = en_words(ln.get('en_ph', ''))
            if 'en_ph' not in ln:
                pass  # 没有英文版的仪轨不查英文音译
            elif sum(n for _, n in ew) != len(ts):
                errs.append(f"{where}：藏文 {len(ts)} 个音节，英文音译估算 {sum(n for _, n in ew)} 个（可用 {{}} 标注）")
            else:
                i = 0
                for k, (w, n) in enumerate(ew):
                    for s in ln['syllables'][i:i + n]: s['en_word'] = k
                    i += n
                ln['en_words'] = [w for w, _ in ew]
            if 'gloss' in ln:
                words, err = parse_gloss(ln['gloss'], ts)
                if err: errs.append(f"{where}：{err}")
                else: ln['words'] = words
            for key in [k for k in ln if k.startswith('t.')]:
                ts_ = [float(x) for x in ln[key].split()]
                if any(b <= a for a, b in zip(ts_, ts_[1:])): errs.append(f"{where}：{key} 时间不是递增的")
                if key != 't.zh' and 'beats' in ln and len(ts_) != len(ln['beats'].split(';')):
                    errs.append(f"{where}：{key} 应有 {len(ln['beats'].split(';'))} 个时间点，现在有 {len(ts_)} 个")
            for key in [k for k in ln if k.endswith('_align')]:
                base = key[:-len('_align')]
                segs, err = parse_align(ln[key], ts, ln.get(base, ''))
                if err: errs.append(f"{where}：{base} 对应{err}")
                else: ln[base + '_segs'] = segs
            if 'beats' in ln:
                beats, err = parse_gloss(ln['beats'], ts)
                if err: errs.append(f"{where}：节拍{err}")
                else: ln['beat_groups'] = beats
    lines = [ln for sec in r['sections'] for ln in sec['lines']]
    for key in sorted({k for ln in lines for k in ln if k.startswith('t.')}):
        miss = [ln['id'] for ln in lines if key not in ln]
        if miss: errs.append(f"{key}：这些句子没有时间点：{'、'.join(miss)}")
    for sec in r['sections']:
        for k in [k for k in sec if k.startswith('t.')]:
            errs.append(f"段落 {sec['id']} 里有 {k}，应该放在某一句下面")
    return errs

if __name__ == '__main__':
    for path in sys.argv[1:]:
        r = parse(path); errs = check(r)
        print(f"{path}: {'没有问题' if not errs else str(len(errs)) + ' 处需要看'}")
        for e in errs: print('  ' + e)
        json.dump(r, open(path[:-4] + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

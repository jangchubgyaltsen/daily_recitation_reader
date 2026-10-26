"""把项目里的源文件（模板、工具、仪轨数据、规划文档、词库索引）复制到仓库的 src/ 里，好用 git 记录每次改动。
共享文件夹仍是工作的地方；这一步只是存一份带历史的副本。build_pages.py 每次发布都会先跑它，
所以网页的每个版本都和生成它的源文件在同一个提交里。录音和词库 mp3 不放进来（太大，发布用的已在 a/ 里）。
用法：python3 tools/sync_src.py <仓库目录>"""
import glob, os, shutil, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dst = os.path.join(sys.argv[1], 'src')
PATTERNS = ['app/template.html', 'tools/*.py', 'tools/*.js', 'tools/*.html', 'rituals/*.txt', 'rituals/*.json',
            'plan/*.md', 'lexicon/bo/index.tsv', 'audio/*.txt']
want = {os.path.relpath(p, root) for pat in PATTERNS for p in glob.glob(f'{root}/{pat}')}
for p in glob.glob(f'{dst}/**/*', recursive=True):  # 项目里删掉的文件，src/ 里也删掉
    rel = os.path.relpath(p, dst)
    if os.path.isfile(p) and rel != 'README.md' and rel not in want: os.remove(p)
for rel in sorted(want):
    os.makedirs(os.path.dirname(f'{dst}/{rel}'), exist_ok=True)
    shutil.copy2(f'{root}/{rel}', f'{dst}/{rel}')
print('src/', len(want), '个文件')

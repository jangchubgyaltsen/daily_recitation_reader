# 源文件

这里是生成网页用的源文件副本，用 git 记录每次改动。日常编辑在项目共享文件夹里进行，
`tools/build_pages.py` 每次发布时会先运行 `tools/sync_src.py`，把最新的源文件复制到这里，
和生成的网页放在同一个提交里。也可以不发布、单独运行 `python3 tools/sync_src.py <仓库目录>` 再提交。

- `app/template.html`：阅读器（界面和全部逻辑）
- `rituals/*.txt`：仪轨数据（人工编辑）；`*.json` 由 `tools/check.py` 生成
- `tools/`：构建、校对、词库脚本
- `lexicon/bo/index.tsv`：藏文发音词库索引
- `plan/`：需求与数据格式说明

录音和词库 mp3 不放在这里，发布用的在仓库根目录的 `a/` 里。

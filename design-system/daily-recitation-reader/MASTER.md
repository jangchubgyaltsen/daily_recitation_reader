# 藏汉课诵阅读器 · 设计系统（B 组）

按 UI UX Pro Max（v2.15）+ Taste（tasteskill v2，app-screens 章节）的流程制定。
注意：本环境不允许执行两个 Skill 自带的脚本（search.py / draw.mjs / inspect.mjs），
因此改为直接读取它们的数据文件（UUPM `data/*.csv`，Taste `library/app.json`）手动完成同样的查询与“发牌”，
检查环节用 Playwright 截图 + 自写的对比度/触控尺寸测量代替 inspect.mjs（Taste 的 “No Chrome or Node 22” 特例允许这样做）。

## 0. 产品判断（UUPM Step 1 / Taste 2.1）

- 产品：个人每日课诵工具（藏文经文 + 音译 + 汉译 + 录音跟读 + 藏历），PWA，离线，主要在 iPhone 上用。
- 人：初学者，每天早晚打开一次，读/听 5–60 分钟；也会在平板、电脑上看。
- 每屏的一个问题（Taste 2.2）：
  - 仪轨库首页：「今天念什么？」 → 最大的东西是今天的藏历日期 + 下一个殊胜日 + 我的组合的「开始念诵」。
  - 阅读页：「这一句怎么念、什么意思？」 → 最大的东西是藏文正文。
  - 藏历：「今天是不是殊胜日、该念什么？」
  - 设置：「我的数据在哪里、怎么备份？」
- 最常做的事：开始念诵某个组合 → 首页一键可达（已具备，保留并强调）。

## 1. Design Audit（原版，按 UUPM 优先级 1→10 + Taste 房规）

| # | 问题 | 依据 | 严重度 |
|---|------|------|--------|
| 1 | 次要文字 #6c7079 放在 #f6f5f1 / 卡片底色上，部分只有 4.4:1 | UUPM `color-contrast` 4.5:1 | CRITICAL |
| 2 | 藏历格子里 9–10px 的小字（节日名、公历日） | Taste「Nothing under 11px」；UUPM 正文 ≥12 | HIGH |
| 3 | 多个可点元素小于 44px：目录胶囊 ~24px、chip ~31px、`.link.small` 36px | UUPM `touch-target-size` | CRITICAL |
| 4 | 圆角混乱：4/6/8/10/12/14/16/999 共 8 种 | Taste §9.4 圆角二选一（紧 4–8 / 软 16–24） | MEDIUM |
| 5 | 小号加字距的分组标题（12px、letter-spacing .1em） | Taste 房规「No tiny tracked labels」 | MEDIUM |
| 6 | 列表分隔用虚线（`dashed`） | Taste §13：虚线只用于图表网格和空位 | MEDIUM |
| 7 | 强调色（青金蓝）铺在导航选中、所有选中 chip、分段控件上，主次不分 | Taste「accent on data + 至多一个控件」 | HIGH |
| 8 | 桌面 1440 宽：首页是一条 760px 的窄列 + 横跨全屏的底部 Tab，三个按钮相距 480px；首屏大片空白 | Taste「first screen was thin」「624–864px column flagged」；UUPM `adaptive-gutters` | HIGH |
| 9 | 首页没有产品的「脸」：只有“仪轨库”三个字，看不出今天的藏历和殊胜日（数据其实都在藏历页里） | Taste「Give the product a face」「one element only this product has」 | HIGH |
| 10 | 深色模式底色带蓝（#16181d），属于 slate 系 | Taste §9.3「No navy and no slate」 | LOW |
| 11 | 按下没有反馈；弹层无进入动画；无 reduced-motion 兜底（除少数） | UUPM `press-feedback`、`reduced-motion` | MEDIUM |

## 2. 方向（Taste 2.3：发牌与选择）

- kind = `workspace`（team hubs and personal homes）→ 可选 style：`editorial-greeting`、`achromatic-ledger`。
- **选 `editorial-greeting`**：这是个人的「家」，每天打开一次，开场应当是一句排好的、带今天事实的问候，而不是数据表；
  `achromatic-ledger` 是给钱和账单的。
- `--keep palette`：App 已有品牌色青金蓝（lapis，藏地佛像与唐卡的青金石），保留；它是蓝（色相 221°），不在 violet/indigo 禁区。
  UUPM 对 Meditation / Religious 查到的是紫色系（#7C3AED），与 Taste 的禁紫规则和现有品牌冲突，不采用；记录在此。
- 这个风格的一招（不动）：**问候即 h1，下面所有数字都用常规字重，坐在一层色阶面板上；没有阴影的卡片。**
- 脸（Its face，三选一）：**「A surface from the product's world」** —— 底色取经页纸（pecha paper）的暖白，面板是同色系低一阶。
- 只有这个产品有的元素（signature）：**「今日」条** —— 首页顶部显示今天的藏历日期、公历日期、下一个殊胜日倒计时，
  若今天有设定的推荐念诵则直接给出「开始念诵」。点它进藏历。

## 3. 设计令牌

| 角色 | 浅色 | 深色 |
|------|------|------|
| ground 页面 | #fbfaf7 | #121212 |
| panel 面板（一阶色差，无边框无阴影） | #f3f1ec | #1c1c1d |
| raised 选中/按下 | #e9e6df | #2a2a2c |
| rule 行分隔 1px 实线 | #e6e3dc | #2a2a2c |
| ink 正文 | #1b1c20 (16.3:1) | #ecebe7 |
| muted 次要 | #575a62 (≥5.5:1 在所有面上) | #a9abb2 |
| accent 青金蓝（只用于：开始念诵按钮、当前句/词高亮、殊胜日以外的数据） | #2d4b8e | #9cb3ec |
| special 殊胜日红（藏红，数据色） | #a3302a | #f08f86 |
| 选中态（chip/分段/Tab） | ink 填充 + ground 字 | 反相 |

- 圆角：**软**一档。面板 20，内部行/输入 12，控件全圆角 999。
- 字体：系统 UI 无衬线一种 + 现有经文字体（藏文 Noto Serif Tibetan、汉文宋体、音译楷体，属内容字体不动）。
- 字号：12 / 14 / 16 / 20 / 24（标题），首页问候 24–28；没有 <11px 的字。
- 字重：400 / 600；700 不用。
- 间距：4 的倍数；面板内边距 20；面板间距 12–16；分区间距 28–32。
- 控件高度：44（触控），桌面工具栏 40。
- 动效：只做反馈（按下 120ms、弹层 220ms 进入/160ms 退出），全部有 `prefers-reduced-motion` 兜底；不做入场动画。

## 4. 布局

- 手机 (≤767)：底部 Tab（3 个，选中 = 墨色文字 + 浅灰胶囊），16px 边距。
- 平板 (768–1023)：底部 Tab 保留，内容列 720，边距 24。
- 桌面 (≥1024)：Tab 变成左侧 220px 的带文字侧栏（open-plane 外壳：在页面底色上，1px 分隔，顶部是产品名），
  首页内容列 880，组合卡片 2 列；阅读页仍是单栏，正文宽度保持 45–75 字的阅读行长。

## 5. 禁用清单（本项目）

渐变、毛玻璃/backdrop-blur、静止卡片阴影、紫/靛、emoji 图标、虚线分隔、小号加字距标签、强调色铺在导航上。

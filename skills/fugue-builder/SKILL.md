---
name: fugue-builder
description: "From-scratch fugue and polyphony composition for ANY musical idiom, no ML model needed: handcrafted subject + scale-degree transposition formulas + constraint-search counterpoint + procedural instrument synthesis, rendered to WAV/MIDI. Use this skill whenever the user wants to compose or generate fugues, canons, chorales, inventions, or any polyphonic/counterpoint music in any style — Baroque tonal, modal, pentatonic or other Chinese scales, Japanese scales, blues, harmonic minor, or a custom scale the user describes — even if they just casually say '帮我写一首赋格' '做一段复调' 'generate a Bach-style piece' '用某某音阶做卡农'. The engine derives counterpoint parameters (step sets, consonance, answer transposition) from the target scale system instead of assuming a fixed style."
---

# Fugue Builder：从零构建任意风格的赋格

## 核心思想

一条赋格分四类素材来源，这个分工决定生成质量的上限，任何风格通用：

| 素材 | 来源 | 原因 |
|---|---|---|
| 主题 | 手写 | 规则能检验主题展开是否合法，产生不了好动机 |
| 答题、低音再入 | 移调公式 | 封闭运算，公式结果优于搜索 |
| 对题与全部自由声部 | 约束搜索（beam search + 罚函数） | 规则密度最高的部分 |
| 间插段模进、终止式 | 手写 | 长程结构靠模板，罚函数管不了几小节外 |

引擎与风格完全解耦：风格由 profile 参数（音阶资源表、协和集、级进定义、移调模式、乐器配方）与手写素材决定。模板内置两个已验证范例 profile（五声民乐、D 小调管风琴），仅作推导参考。

## 工作流

### 1. 需求分析

从用户的描述确定目标体系：调式或音阶、速度情绪、编制（几件什么乐器）、特殊要求（平行五度政策、装饰音风格）。用户没说的按该体系的音乐惯例定，并在交付时说明你的选择。

### 2. 推导 profile

这是本 skill 的核心步骤，完整规程在 [references/counterpoint.md](references/counterpoint.md) 第一节，必读。速览：

- scale 资源表：目标体系跨八度连续数组，必须包含全部调性借用音（导音、皮卡迪三度、答题移调产物），缺列会崩溃或误报
- step 级进集、挂留解决集：通常省略，引擎从 scale 自动推导
- 答题公式二选一：音阶自足体系用 degree（音阶级平移，五声宫到徵 +3）；主题含导音借用的调性体系用 semitone（半音移调会把导音正确映射到新调）
- 风格开关：间插段平行五度放行与否、调式和弦奖励与否
- 声部域：scale 子集按音区分配，通常排除借用音
- 乐器与混响配方：见 [references/synthesis.md](references/synthesis.md)

### 3. 手写素材

主题（8 小节 64 个八分位）、间插段模进、终止式，全部按目标风格的惯例设计。主题必须给特征动机与高点。手写段引擎不查规则，写完自查拍点协和。

### 4. 运行与验证

复制 `scripts/fugue_template.py`，替换 profile 与素材区（引擎区不动），在 uv 临时环境安装 numpy、matplotlib、midiutil 后运行。运行约 20 秒，产出搜索罚分、独立验证器报告、WAV、MIDI、钢琴卷帘谱 PNG。

验证目标：偏音 0、严格段平行五八 0、未准备拍点不协和 0 到 2、未级进解决 0 到 2、旋律大跳 0。不达标时按 counterpoint.md 第四节的调参表迭代，先调细节激励参数，不动级进奖励。

### 5. 渲染质检与交付

按 synthesis.md 第六节检查 WAV（无削波、声部递进的能量曲线、结尾衰减）。交付 MP3 加 WAV 加谱面 PNG 加 MIDI，说明结构（主题进入点、公式部分、搜索部分）与验证报告。

## 踩坑清单（全部来自真实翻车）

1. 细节机制零触发：弱位不协和如果设为罚分，搜索永远选全协和路径，经过音挂留一个不出现。弱位必须给小奖励，细节密度靠目标函数主动引导，规则允许与搜索愿意用是两回事
2. beam 枯竭在固定声部：旋律跳进禁令与不协和 flag 义务只能加在搜索声部上。手写素材的合法八度跳（音阶级距离 5）会让整条 beam 在一步内全灭
3. beam 枯竭在终止接驳：三个声部一步跳到手写终止音必然撞约束。引导罚提前 10 个位置铺路，终止小节内硬淘汰降级为大罚兜底
4. 固定声部被记伪违例：责任判定只认搜索声部，固定声部无选择权
5. scale 缺列：借用音不入资源表，轻则误报偏音，重则索引崩溃；音阶数组漏音会推导出假步长污染级进集
6. 挂留奖励过强：-3 会产出 78 次挂留，全曲浑浊，-2 左右密度健康
7. 搜索域含借用音：搜索会把导音当装饰音高频使用，拍点摩擦从 2 处涨到 16 处

## 环境规范

临时任务用 uv 在系统临时目录建虚拟环境（`uv venv /tmp/<name>` 后 `uv pip install --python /tmp/<name>/bin/python numpy matplotlib midiutil`），不在系统 Python 装第三方库。MP3 转换用 ffmpeg（`-codec:a libmp3lame -b:a 192k`）。

## 文件

- `scripts/fugue_template.py`：可运行模板，引擎区经过两套体系三个作品验证，不要改引擎区
- `references/counterpoint.md`：参数推导规程、规则形式化、罚函数调参表、验证清单
- `references/synthesis.md`：乐器配方参数、混响空间、新乐器扩展方法、渲染质检

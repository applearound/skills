---
name: jj-usage
description: 介绍 jujutsu (jj) 版本控制系统的核心概念与日常命令用法。当用户在 jj 仓库中操作（查看状态、提交、改写历史、处理书签与推送、撤销误操作）、询问 jj 命令怎么用、需要把 git 习惯映射到 jj、使用 colocated 仓库，或提到 jujutsu、jj、jj-vcs 时，使用本技能。
---

# jj：Git 兼容的版本控制系统

[jj](https://github.com/jj-vcs/jj) 是 Rust 实现的分布式版本控制系统，可以直接拿现有 git 仓库当后端，远端、GitHub 协作照常。本技能的命令语义核对自 jj 0.46 的 `jj help`，与旧文档不一致处已标注；本机验证用 `jj --version`。

## 心智模型

和 git 的四个关键差异，理解了它们，大部分命令的行为都能推出来：

1. 工作副本就是一个提交。每条 jj 命令执行前会先把工作副本快照进当前提交 `@`。没有暂存区，不存在「未提交的修改」这个状态：改完文件，改动已经在 `@` 里，缺的只是提交说明。
2. 提交默认可变。改说明、改内容、拆分、重排都是常规操作，change id 跟着提交演化，改写历史不算事故。
3. 一切操作记录在 operation log 里。误操作先 `jj undo`，不满意再从 `jj op log` 挑时间点恢复，仓库层面很难丢数据。
4. 冲突可以入历史。rebase 撞出冲突时，jj 把冲突当作提交内容快照下来继续走，稍后解决即可，不会被卡住。

## 初始化

| 场景 | 命令 |
| --- | --- |
| 全新仓库 | `jj git init` |
| 已有 git 仓库原地启用，git 与 jj 命令可混用 | `jj git init --colocate` |
| 克隆 | `jj git clone <url>` |

## 日常循环

没有 add 和 commit 的区分，改动自动落在 `@`：

```bash
jj st                    # 看状态，顺带触发快照
jj diff                  # 看 @ 的改动
jj describe -m "标题"    # 给 @ 补提交说明
jj new                   # 在 @ 上开新提交，之后的改动进入它
```

`jj commit -m "msg"` 等于 describe 加 new 一步到位。

回头改某个已描述的提交：`jj edit <rev>` 把工作副本切过去，直接改文件，快照会写回该提交，相当于自动 amend。

## 看历史

`jj log` 画提交图，用 revset 表达式过滤：

```bash
jj log -r ::@           # @ 的全部祖先
jj log -r 'trunk()..@'  # 远端主干之后属于我的提交
```

`@` 是工作副本提交，`@-` 是父提交，`trunk()` 解析到远端主干（main 等）。revset 速查见 references/cookbook.md。

## 书签与推送

bookmark 对应 git 的 branch。0.25.0 起 `jj branch` 改名 `jj bookmark`，旧教程里的 `jj branch` 按此换算。

```bash
jj bookmark create feature-x -r @   # 在 @ 建书签
jj bookmark track feature-x@origin  # 首次推送前声明同步，一次即可
jj git push                         # 推送已跟踪书签指向的提交
jj git push --change @              # 为当前提交自动生成 push- 前缀书签并自动跟踪，适合直接开 PR
jj git fetch                        # 拉取远端
jj bookmark move feature-x --to @   # 书签前移到新提交
```

0.46 起默认 push 拒绝凭空创建远端书签，必须先 track，旧文档里的 `--allow-new` 已移除。推送时直接指定新名字用 `jj git push --named <名>=<rev>`。GitHub 工作流细节见官方 GitHub 协作文档。

## 纠错

```bash
jj undo                        # 撤销上一条 jj 操作
jj op log                      # 完整操作历史
jj restore                     # 丢弃 @ 的改动，内容回到父提交
jj restore --from <rev> <path> # 从任意提交拷回文件
```

## 深入

历史改写（squash、absorb、split、rebase 的场景与参数）、revset 速查、冲突处理、多工作区、colocated 仓库注意事项、常用配置：读 references/cookbook.md。

## 外部资源

| 资源 | 链接 |
| --- | --- |
| 官方文档 | https://docs.jj-vcs.dev/latest/ |
| 官方教程 | https://docs.jj-vcs.dev/latest/tutorial/ |
| 与 git 的概念对比 | https://docs.jj-vcs.dev/latest/git-comparison/ |
| git 兼容与 colocated | https://docs.jj-vcs.dev/latest/git-compatibility/ |
| revset 语言 | https://docs.jj-vcs.dev/latest/revsets/ |
| operation log | https://docs.jj-vcs.dev/latest/operation-log/ |
| GitHub 协作 | https://docs.jj-vcs.dev/latest/github/ |
| FAQ | https://docs.jj-vcs.dev/latest/faq/ |
| 源码仓库 | https://github.com/jj-vcs/jj |
| 社区入门教程（Klabnik，基于旧版 jj，命令有出入） | https://steveklabnik.github.io/jujutsu-tutorial/ |
| git 用户迁移教程（2025-10） | https://www.stavros.io/posts/switch-to-jujutsu-already-a-tutorial/ |

本机装有 jj 时，`jj help -k <主题>` 可打开内置专题文档，可选主题有 bookmarks、config、filesets、glossary、revsets、templates、tutorial，内容与官方文档同源。

---
name: rtk
description: 教没有 rtk hook 集成的 agent 手动使用 rtk CLI 压缩命令输出。当要执行输出会进入上下文的 shell 命令（git、测试、构建、lint、类型检查、docker/kubectl、文件查看与搜索、curl），或用户提到 rtk、省 token、压缩命令输出、上下文太大时，使用本技能。
---

# rtk：手动压缩命令输出

[rtk](https://github.com/rtk-ai/rtk) 是一个 CLI 代理，Rust 单二进制，开销约 10ms。命令经它执行后，输出先过滤再进入上下文：进度条、通过项、样板文本被去掉，只留有效信息。官方 hook 只覆盖部分 agent；没有 hook 的 agent 自己给命令加 `rtk` 前缀，效果相同。

rtk 只作用于 shell 命令输出。agent 内置的文件读取、搜索工具不经过它，无需处理。

## 前置检查

```bash
rtk --version
```

有版本号即可用。缺失时安装：`brew install rtk`（Windows 用 `winget install rtk-ai.rtk`）。注意 crates.io 上有同名错误包：`rtk gain` 能显示节省面板才是正确的包。

## 怎么加前缀

默认规则：输出会进入上下文的命令都加 `rtk` 前缀。rtk 认识的命令走专用过滤器（git、主流测试框架、构建、lint、包管理、docker、kubectl、aws 等均有内置）；不认识的命令透传原样输出，加前缀没有破坏风险。过度加前缀的代价只有约 10ms，漏加的代价是上下文污染，所以宁可多加。

git 写操作返回极简确认：`rtk git commit -m "msg"` 输出 `ok abc1234`，`rtk git push` 输出 `ok main`。

不确定怎么写时问 `rtk rewrite`。它是全部改写规则的单一事实来源，官方 hook 只是它的薄封装。退出码 0 或 3 且有输出即改写结果（3 为 advisory），退出码 1 且无输出表示不改写：

```bash
rtk rewrite "cat README.md"            # rtk read README.md，cat 映射到 rtk read
rtk rewrite "uv run pytest"            # uv run rtk pytest，嵌进 wrapper 内侧保留环境语义
rtk rewrite "git status | grep main"   # git status | rtk grep main，改写产出上下文的管道尾段
rtk rewrite "cd /tmp && ls"            # cd /tmp && rtk ls，复合命令逐段改写
```

已带 rtk 前缀的命令经 rewrite 原样返回，不会双重包装。

## rtk 自带的文件与搜索工具

| 目的 | 命令 |
| --- | --- |
| 看目录 | `rtk ls .` |
| 读文件 | `rtk read file.rs`（默认全量同 cat；`-l aggressive` 只留签名，`-m 40` 给 40 行结构预览） |
| 快速了解文件 | `rtk smart file.rs`（两行启发式摘要） |
| 找文件 | `rtk find "*.rs" .`（支持原生 find 参数） |
| 搜文本 | `rtk grep -r "pattern" .`（透传原生参数，递归要自带 `-r`）；`rtk rg`、`rtk ast-grep` 同理 |
| 比较文件 | `rtk diff a b`（退出码 0 相同、1 不同、2 读取错误） |
| 看 JSON | `rtk json config.json --keys-only`（只留键；默认仅截断长值） |
| 看日志 | `rtk log app.log`（重复行折叠计数） |
| 看环境变量 | `rtk env -f AWS` |
| 请求 URL | `rtk curl <url>`（截断响应，自动识别 JSON 结构） |

## 通用包装器

rtk 没有专用过滤器的长输出命令，用包装器控制保留内容。参数按 argv 原样传递，不展开 glob、变量、管道操作符；需要 shell 语法时用 `-c` 或 `--shell`（默认 sh）：

```bash
rtk err make build                       # 只留错误和警告
rtk test python -m pytest                # 只留失败的测试
rtk summary mvn package                  # 执行后附启发式摘要
rtk proxy make install                   # 不过滤，但计入节省统计
rtk run ./scripts/gen.sh                 # 原始执行，不过滤不统计
rtk run -c 'cd pkg && go test ./...'     # 经 sh 执行命令字符串
rtk test --shell sh 'cargo test && cargo clippy'
rtk pipe -f cargo-test                   # 从 stdin 读取，过滤后输出
```

## 不加前缀的场景

- 交互式命令（REPL、需确认输入的安装器）。
- 需要逐字节精确的输出：算校验和、与固定文本全等比对。
- 输出要交给下游程序解析，下游依赖原始格式：用原命令或 `rtk run`。
- 需要原命令的精确行为：包装器可能调整输出模式，实测 `rtk pytest -v` 按非冗余模式捕获，看不到逐个测试的 PASSED 行。此时用 `rtk run` 重跑。
- 输出只有一两行的琐碎命令（`rtk rewrite "echo hi"` 对它也返回 1）。

## 被截断的输出怎么找回

命令失败或输出被裁剪时，rtk 把完整输出存进本地库并打印提示。照抄提示执行即可取回，无需重新执行命令：

```text
FAILED: 2/15 tests
[full output: rtk recall 3f9c2a81d4e7]
```

```bash
rtk recall --list
rtk recall <hash> --full
rtk recall <hash> --from 200
rtk recall <hash> --grep "timeout"
```

## 选项与统计

- `--ultra-compact` 进一步压缩。不要用短写 `-u`，与 git 的 `--set-upstream` 冲突。
- `-v`、`-vv` 放在子命令前面，如 `rtk -vv git status`，stderr 显示过滤详情。
- `rtk gain` 看总节省，`--daily`、`--graph` 看明细；`rtk discover` 找出漏加前缀的命令；`rtk session` 看各会话采用率。token 数按字节除以 4 估算。

## 更多

行为以本机 `rtk --help` 为准：`rtk read` 的 `--level`、`rtk grep` 的 `-r` 等 0.51 实际行为，官方文档尚未覆盖。变更史与规则源码（`src/discover/registry.rs`）见仓库：https://github.com/rtk-ai/rtk

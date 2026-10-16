# jj 进阶手册

SKILL.md 的延伸，命令语义核对自 jj 0.46 的 `jj help`。

## 历史改写

按意图选命令：

| 意图 | 命令 |
| --- | --- |
| 把 @ 的改动并入父提交 | `jj squash`，全量并入；`-i` 交互选 hunk |
| 在任意两个提交间搬改动 | `jj squash --from <X> --into <Y>` |
| 改动按行归属自动回填到祖先 | `jj absorb`，类似 git-absorb，归属不明的行留在原处 |
| 把一个提交拆成两个 | `jj split`，diff 编辑器右侧留下第一半；`jj split <paths>` 先按路径粗分 |
| 调整提交位置 | `jj rebase` |
| 删除提交 | `jj abandon <rev>`，子提交自动重挂到其父 |

`squash` 把源提交搬空后，源提交自动消失，想保留空壳加 `--keep-emptied`。合并说明默认拼接两边，`-u` 改用目标提交的说明、丢弃来源的。`absorb` 的结果用 `jj op show -p` 复核。

### rebase 的三种范围

```bash
jj rebase -s <rev> -d <dest>   # rev 连同全部后代搬到 dest 下
jj rebase -r <rev> -d <dest>   # 只搬 rev，其后代重挂到 rev 原来的父上
jj rebase -b <rev> -d <dest>   # 整条分支相对 dest 的祖先平移
```

另有 `-A <rev>`、`-B <rev>`（insert-after、insert-before）把提交插到某个提交之后或之前，用来调整栈内顺序。

### 观察改写结果

```bash
jj obslog                         # @ 的演化链，每次快照、squash 前后一目了然
jj obslog -r <rev>                # 指定提交的演化
jj interdiff --from <a> --to <b>  # 同一提交两个版本的净差异
```

## revset 速查

运算符：`::x` 全部祖先，`x::` 全部后代，`x..y` 在 y 且不在 x 祖先里的提交，`&` 交集，`|` 并集，`~` 差集。

| 表达式 | 指向 |
| --- | --- |
| `@`、`@-`、`@--` | 工作副本、父提交、祖父提交 |
| `root()` | 虚拟根提交 |
| `trunk()` | 远端主干，main、master 等 |
| 书签名，如 `main` | 该书签指向的提交 |
| `bookmarks()`、`remote_bookmarks()` | 本地书签、远端书签 |
| `mine()` | 作者为当前用户的提交 |
| `heads(x)`、`parents(x)`、`children(x)` | 头、父、子 |
| `empty()` | 空提交，配合 `jj abandon -r 'empty()'` 一键清理 |
| `description("字串")` | 说明含字串的提交 |

完整语言见官方 revset 文档：https://docs.jj-vcs.dev/latest/revsets/

## 冲突

- 冲突被快照成提交内容，`jj log` 里看得到，带着冲突继续 rebase、继续干活都行。
- `jj resolve` 逐文件调外部三方合并工具；也可以直接编辑文件里的冲突标记，改完执行任意 jj 命令触发快照，冲突状态即消除。
- 默认推送拒绝含冲突的提交，强行推送要 `--allow-conflicts`，一般别用。

merge 提交用 `jj new <a> <b>`，直接以两个提交为父创建。

## 多工作区

```bash
jj workspace add ../work2   # 同一提交图的第二个工作副本
jj workspace list
jj workspace forget <name>
```

一个仓库两处挂改动，两边的 @ 互不干扰快照。

## colocated 仓库注意

- git 与 jj 命令可以混用，jj 在每条命令前自动 import git 侧的 refs 与 HEAD 变化。
- 切换提交用 `jj edit`，别用 `git checkout`：它移动 HEAD，jj 导入后工作副本会跟着重置。
- git 侧新建的分支 import 后成为 jj 书签，jj 推送的书签对 git 也是普通分支，双向同名对应。

## 配置

```bash
jj config path --user                  # 用户级配置文件路径
jj config set --repo user.name "名字"  # 仓库级设置
jj config set --user ui.diff.tool <工具名>
```

colocate 或 clone 时 user.name、user.email 会尝试从 git 配置导入。diff、merge 工具的配置细节见 https://docs.jj-vcs.dev/latest/config/

# AGENTS.md

本文件向在此仓库工作的 coding agent 说明仓库约定。

## 仓库用途

存放个人常用的 agent skills。仓库结构符合 [vercel-labs/skills](https://github.com/vercel-labs/skills) CLI 的发现规则，通过以下命令安装到本机：

```bash
npx skills add applearound/skills
```

## 目录结构

所有技能放在 `skills/` 目录下，每个技能一个子目录，不要放在其他位置。CLI 从 `skills/` 向下最多扫描三层。

```text
skills/
  <skill-name>/
    SKILL.md          # 必需
    references/       # 可选，按需加载的参考文档
    scripts/          # 可选，辅助脚本
    assets/           # 可选，模板等静态资源
```

## 新增或修改技能

1. 在 `skills/` 下新建目录，目录名即技能名，小写 kebab-case。
2. SKILL.md 的 YAML frontmatter 必须包含 `name` 和 `description`，`name` 必须与目录名一致。
3. `description` 写清楚两件事：技能做什么、什么情况下触发。这是 agent 判断是否加载该技能的主要信号，宁可写得具体，不要写得含糊。
4. SKILL.md 正文控制在 500 行以内，细节内容拆到 `references/` 子文档，在正文中说明何时读取。
5. 同步更新 README.md 的技能列表表格。

## 验证

提交前在仓库根目录执行本地验证，不需要推送：

```bash
npx skills add ./ --list
```

输出中能看到改动涉及的技能即格式正确。

## Git 约定

- main 分支直接提交推送，提交信息用英文，一行说明改动。
- 本仓库已配置本地 `core.sshCommand` 指向 Windows OpenSSH，推送直接 `git push` 即可。
- 提交者身份配置在仓库本地（applearound 的 GitHub noreply 邮箱），不要改动。

## 其他

- `skills/test-skill` 是验证安装链路的临时技能，链路已验证通过，可随时删除。
- README.md 面向仓库使用者，本文件面向在此工作的 agent，两类内容不要混写。

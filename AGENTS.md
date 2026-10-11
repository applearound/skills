# AGENTS.md

本文件向在此仓库工作的 agent 说明仓库约定。

## 仓库用途

存放常用的 agent skills。仓库结构符合 [vercel-labs/skills](https://github.com/vercel-labs/skills) CLI 的发现规则，可通过以下命令安装到用户机器：

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

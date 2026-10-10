# 个人 Skills 仓库

存放我个人常用的 agent skills，通过 [vercel-labs/skills](https://github.com/vercel-labs/skills) CLI 一条命令安装到本机。

## 安装

```bash
# 安装仓库中的技能（交互式选择）
npx skills add applearound/skills

# 只安装指定技能
npx skills add applearound/skills --skill test-skill

# 全局安装（装到用户目录，所有项目可用）
npx skills add applearound/skills -g

# 更新已安装的技能
npx skills update
```

## 技能列表

| 技能 | 说明 |
| --- | --- |
| [test-skill](skills/test-skill/) | 临时测试技能，验证安装链路用，链路验证完成后可删除 |

## 仓库结构

```text
skills/
  <skill-name>/
    SKILL.md          # 必需，frontmatter 含 name 和 description
    references/       # 可选，按需加载的参考文档
    scripts/          # 可选，辅助脚本
```

每个技能一个目录，放在 `skills/` 下。目录名必须与 SKILL.md frontmatter 中的 `name` 一致（小写 kebab-case）。新增技能后在本 README 的技能列表里补一行。

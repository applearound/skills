---
name: single-html
description: 用 petite-vue 在单个 HTML 文件内构建带交互的页面，无需任何构建步骤。当用户要求单文件 HTML 页面、一个 HTML 文件搞定、无构建的轻量交互、可交互的演示页或原型、小工具页面，或提到 petite-vue、轻量版 Vue 时使用。
---

# Single HTML（petite-vue 单文件页面）

用 [petite-vue](https://github.com/vuejs/petite-vue) 给单个 HTML 文件加 Vue 语法的响应式交互。它约 6KB，直接操作真实 DOM，没有虚拟 DOM 和构建步骤。适用场景：单文件交付的页面、快速原型、演示页、轻量小工具。

## 何时不用这个方案

需求属于以下情况时，改用标准 Vue 或其他完整框架，不要用 petite-vue：

- 重交互的 SPA，需要组件工程化、路由、状态管理。
- 需要 SSR、渲染函数、Transition、Teleport。
- 页面有严格 CSP（petite-vue 用 `new Function` 求值表达式，会被拦截）。

## 最小可用骨架

直接复制这个骨架开始。本地预览用浏览器打开即可，脚本来自 CDN，需要网络。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Single HTML</title>
  <style>[v-cloak] { display: none; }</style>
</head>
<body>
  <div v-scope="{ count: 0, text: '' }" v-cloak>
    <p>{{ count }}</p>
    <button @click="count++">加一</button>
    <input v-model="text">
    <p>输入的是：{{ text }}</p>
  </div>

  <script src="https://unpkg.com/petite-vue" defer init></script>
</body>
</html>
```

三个要点：

- `v-scope` 标记受 petite-vue 控制的区域，值是内联对象字面量，里面放状态和方法。
- `defer` 让脚本在 HTML 解析完后执行，`init` 属性让 petite-vue 自动初始化页面上所有带 v-scope 的元素。
- `v-cloak` 配合 CSS 隐藏模板，避免脚本加载前露出原始的 `{{ }}` 插值。

## 初始化的两种写法

骨架用的是自动初始化，暴露全局变量 `PetiteVue`。手动初始化用 ES module 写法，能传根作用域和全局状态：

```html
<script type="module">
  import { createApp, reactive } from 'https://unpkg.com/petite-vue?module'

  const store = reactive({
    count: 0,
    get plusOne() { return this.count + 1 },
    inc() { this.count++ },
  })

  createApp({ store }).mount()
</script>

<div v-scope>
  <p>{{ store.count }} / {{ store.plusOne }}</p>
  <button @click="store.inc">加一</button>
</div>
```

- `createApp(数据对象)` 的参数是根作用域，页面上所有表达式都能访问。
- `reactive()` 创建全局状态单例，可以多个 v-scope 区域共享。
- `mount()` 不带参数处理整个 body；`mount('#选择器')` 限制处理范围。页面含不可信 HTML 时必须用显式目标，只处理自己控制的区域，防止表达式注入。
- 同一页面可以 createApp 多次，分别 mount 到不同区域。

## 指令速查

Vue 兼容、直接可用的：`{{ }}` 插值、`v-bind` 与 `:` 简写（含 class 和 style 特殊处理）、`v-on` 与 `@` 简写（含全部事件修饰符）、`v-model`（所有输入类型）、`v-if` / `v-else` / `v-else-if`、`v-for`、`v-show`、`v-html`、`v-text`、`v-once`、`v-pre`、`v-cloak`、模板 ref、`nextTick()`。

petite-vue 独有的：

- `v-scope` 定义作用域。
- `v-effect` 执行响应式内联语句：`<div v-effect="$el.textContent = count">`，依赖变化时自动重跑。
- 生命周期事件 `@vue:mounted` 和 `@vue:unmounted`，`vue:` 前缀必须有。
- 表达式里的 `$el` 指当前绑定元素，不是组件根元素。

## 复用逻辑与模板

petite-vue 没有组件系统，组件简化为返回作用域对象的函数，模板复用用 `$template` 指向 `<template>` 元素：

```html
<template id="counter-template">
  <p>{{ count }}</p>
  <button @click="inc">加一</button>
</template>

<div v-scope="Counter({ initialCount: 1 })"></div>
<div v-scope="Counter({ initialCount: 2 })"></div>

<script type="module">
  import { createApp } from 'https://unpkg.com/petite-vue?module'

  function Counter(props) {
    return {
      $template: '#counter-template',
      count: props.initialCount,
      inc() { this.count++ },
    }
  }

  createApp({ Counter }).mount()
</script>
```

## 明确不存在的能力

写代码前过一遍，避免顺手写出跑不了的代码：

- 没有 `ref()`、`computed()`，状态用普通对象字面量，派生值用 `get xx()` getter。
- 没有虚拟 DOM 和渲染函数，没有 SFC。
- Map、Set 等集合类型没有响应性。
- 没有 Transition、KeepAlive、Teleport、Suspense。
- `v-for` 不支持深度解构，不支持 `v-on="对象"` 和 `<component :is>`。

## CDN 地址

原型阶段用短地址 `https://unpkg.com/petite-vue`。交付时固定版本、用完整路径，避免解析和跳转开销：

- 全局构建：`https://unpkg.com/petite-vue@0.4.1/dist/petite-vue.iife.js`，暴露 `PetiteVue` 全局变量，支持 `init` 自动初始化。
- ESM 构建：`https://unpkg.com/petite-vue@0.4.1/dist/petite-vue.es.js`，必须配 `<script type="module">`。

## 需要更多信息时

先读本目录的 `references/petite-vue-readme.md`，这是上游官方 README 的完整快照，离线可用。自定义指令、自定义分隔符、安全与 CSP 的细节都在里面。快照覆盖不到的，去线上找：

- 官方仓库与文档：https://github.com/vuejs/petite-vue
- 官方示例集：https://github.com/vuejs/petite-vue/tree/main/examples

---
name: wechat-post-builder
description: 把素材整理成微信公众号推文并送进草稿箱的完整流程，覆盖图片取票上传、封面生成与去水印、简谱与配乐自制、文案撰写与去 AI 味、言序建稿与发布。当用户要求「整理成待发布的公众号推文」「发到公众号草稿箱」「做个吸睛封面」「去掉水印」「去掉 AI 味」「生成带指法简谱并配乐」时应使用本 skill。不负责群发。
agent_created: true
---

# 公众号推文成品流水线

## 用途与边界

把一份素材（曲谱、图片、文字）做成一篇可直接进公众号草稿箱的文章：素材自制 → 文案 → 去 AI 味 → 建稿 → 发布。

发布环节沿用连接器技能 `yanxu-publisher` 的规范；本 skill 负责它之外的编排，重点是**图片上传通道**、**封面/曲谱/配乐的本地生成**、**文案质量**三块。

边界：只写到草稿箱，不群发。音频、音乐播放器、投票、超链接等公众号原生组件无法通过接口写入，必须在后台手动插入。

## 阶段路由

| 阶段 | 内容 | 何时可跳过 | 详细文档 |
|---|---|---|---|
| 0 | 确认公众号、样式主题、是否立即发布 | 单账号且用户已说「直接发」时简化 | `references/yanxu-api.md` |
| 1 | 素材准备：图片上传、封面、曲谱、配乐 | 用户已提供可用图片时跳过生成 | `references/assets-generation.md` |
| 2 | 文案撰写与去 AI 味 | 用户提供成稿时只做核对 | `references/writing-and-humanizer.md` |
| 3 | 建稿（`create_article` → `info_id`） | 不可跳过 | `references/yanxu-api.md` |
| 4 | 发布到草稿箱（`publish_article`） | 用户说「待发布 / 先别发」时**必须停在此步之前** | `references/yanxu-api.md` |
| 5 | 交付与后台待办清单 | 不可跳过 | 本文末 |

## 硬约束（每次执行前先过一遍）

1. **绝不把本地路径写进 `image.url` 或 `cover_img`。** 服务端读不到本机文件，图片会静默丢失。必须先取一次性上传通道，把图片传成 `file_path`（形如 `mcp/20261106/xxxx.jpg`、`cover/20261106/xxxx.jpg`）再建稿。
2. **一张票对应一张图。** `get_upload_channel` 返回一次性 ticket，5 分钟过期；N 张图取 N 次票，不能复用。
3. **体积**：正文图 ≤1MB、封面 ≤2MB。生成后先检查再提交。
4. **封面 2.35:1**，把标题文字直接写进生图 prompt；裁切时优先用取景偏移避开右下角 AI 水印，不要指望 AI 二次编辑（会重绘构图且水印仍在）。
5. **音频无法通过接口写入。** 交付本地 mp3，正文留一节说明，并在括号里写后台插入提示，排版时删除。
6. **正文图 >2 张时发布为异步**，返回 `async=true` / `status=0 (pending)` 属正常，稍后到后台或发布记录确认。
7. **不复用历史 ID**：`account_id` / `theme_id` / `info_id` 一律取本次工具实时返回值。
8. **建稿与发布分两步**：默认建稿后向用户复述标题 + `info_id` + 目标公众号 + 主题，等确认再发布；仅当用户明确说「直接发到草稿箱」时可连做。
9. **文案必须核对事实**：数字、时长、段落结构、逐图讲解要与谱面或素材一致；发现矛盾先改文案，不要照抄旧稿。

## 执行流程

### 阶段 0 · 定目标

调用 `list_wechat_accounts`，必要时 `list_theme_styles`。确认目标公众号、样式主题、是否立即发布、是否要求封面 / 配乐 / 特定钩子。记录 `account_id` 与 `theme_id`。

### 阶段 1 · 素材

按 `references/assets-generation.md` 产出封面（2.35:1、无水印、≤2MB）、正文配图（逐张 ≤1MB），以及可选的曲谱页与示范音频。

随后按 `references/yanxu-api.md` 的取票上传流程逐张上传，**保存每张返回的 `file_path`**，形成「本地文件 → 服务端路径」映射表。可直接使用 `scripts/upload_images.py`。

### 阶段 2 · 文案

按 `references/writing-and-humanizer.md` 组织章节、写导语与钩子，再逐条过 Humanizer-zh 检查点。把去 AI 味当作编辑动作而非删词：优先保信息与确定程度，其次才是表达。

### 阶段 3 · 建稿

组装扁平 payload（`title` / `abstract` / `intro` / `cover_img` / `chapters` 同级，`chapters` 不要套 `content` 包裹）：

```json
{
  "title": "《致爱丽丝》完整版简谱：三页弹完整首",
  "abstract": "三页简谱，A 段主题、B 段上行模进、A 段再现加尾声，共 24 小节。",
  "cover_img": "cover/20261106/1ab41a6d9c61.jpg",
  "intro": "原曲是回旋曲式，只弹主题相当于只唱了一句副歌……",
  "chapters": [
    {
      "type": "chapter",
      "title": "第 1 页：1–7 小节",
      "blocks": [
        { "type": "image", "url": "mcp/20261106/0ef698ecaa0d.jpg", "alt": "简谱 第1页" },
        { "type": "paragraph", "content": "开头 3 #2 3 #2 3 #2 是十六分音符……" }
      ]
    }
  ]
}
```

约束：`title` ≤30 字、`abstract` ≤100 字、`chapters` 非空；块只有 `paragraph` / `image` / `list` / `table` 四种；`intro` 与章节 `title` 不要重复写成块，否则出现两层标题。保存返回的 `info_id`。

### 阶段 4 · 发布

按硬约束第 8 条决定是否等待确认。调用 `publish_article`，传入 `info_id`；多账号必填 `account_id`，账号无默认样式时必填 `theme_id`。记录返回的异步标记。

### 阶段 5 · 交付

说明稿件状态（已发布 / 待发布）、`info_id`、图片数量，以及仍需后台手动完成的事项（插入音频或音乐、删除排版提示括号、群发）。用 `present_files` 展示封面、谱面、音频与文案存档。

## 交付前核对

- [ ] 每张图片都已上传，`image.url` 是服务端 `file_path`，无本地路径残留
- [ ] 正文图 ≤1MB、封面 ≤2MB
- [ ] 封面无水印、2.35:1、标题未被裁掉
- [ ] `title` / `abstract` 未超字数，`chapters` 为扁平结构
- [ ] 文案过完去 AI 味清单，数字 / 结构 / 逐图讲解与素材一致
- [ ] 文末钩子是具体动作（评论区留名、点赞、关注），不是抒情收尾
- [ ] 后台待办事项已明确告知用户
- [ ] 文案存档为本地 `.md`，脚本与源 HTML 可复现成品

## 常见坑速查

| 现象 | 原因 | 处理 |
|---|---|---|
| 草稿箱文章没有图片 | 把 `D:\...` 本地路径写进了 `image.url` | 重新取票上传，用 `file_path` 重建稿件 |
| 上传第二张图失败 | 复用了同一个 ticket | 每张图重新调 `get_upload_channel` |
| 封面右下角有「AI生成」水印 | 生图工具自带水印 | 裁切时上移取景避开；已存在则用 `prep_images.py cover --dewatermark` |
| AI 二次编辑去水印后构图变了 | 图生图会重绘整张图 | 不要用 AI 编辑去水印，改用像素补丁 |
| 简谱页面大片留白、谱面竖着堆叠 | flex 未写 `flex-direction:row`，或容器用了 `flex:1` | 见 `references/assets-generation.md` |
| 文章里音乐播放器没出现 | 接口不支持音频块 | 后台「插入 → 音频」手动添加 |
| 发布后草稿箱暂时看不到 | >2 张图走异步 | 稍后刷新或查发布记录 `status=1` |

## 资源索引

- `scripts/upload_images.py` — 用 ticket 列表批量上传图片，输出 `file_path` 映射（标准库，无依赖）
- `scripts/prep_images.py` — 封面裁 2.35:1 / 去水印 / 谱面裁白边 / 体积检查
- `references/yanxu-api.md` — 工具参数、取票上传流程、异步发布与错误恢复
- `references/assets-generation.md` — 环境探测、封面 / 简谱 / 配乐生成方法与排版坑
- `references/writing-and-humanizer.md` — 推文结构、钩子、Humanizer-zh 31 条检查点与事实核对
- `assets/article_template.md` — 推文文案骨架模板
- `assets/jianpu_renderer.py`、`crop_white.py`、`make_audio.py` — 简谱与配乐可改模板
- `assets/sample_article.md` — 通过去 AI 味核对的成稿范例

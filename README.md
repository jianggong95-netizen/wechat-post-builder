# wechat-post-builder

一个 WorkBuddy 用户级 Skill：把素材整理成微信公众号推文，并送进公众号草稿箱。

## 它解决什么

这套流程覆盖的不只是「发布」那一步，而是从素材到成稿的完整链路：素材自制与上传 → 文案撰写与去 AI 味 → 建稿 → 发布 → 交付待办。重点沉淀了几个容易反复踩的坑：

- 图片必须先通过一次性上传通道传成服务端 `file_path`，写本地路径会让图片静默丢失
- 一张 ticket 只对应一张图，5 分钟过期
- 封面 2.35:1、无水印，正文图 ≤1MB、封面 ≤2MB
- 音频无法通过接口写入，只能在公众号后台手动插入
- 正文图超过 2 张时发布为异步
- 「待发布」时必须停在 `info_id`，不要连着做发布

## 目录结构

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 阶段路由、硬约束、建稿 payload 骨架、交付核对清单、常见坑速查 |
| `references/yanxu-api.md` | 言序工具参数、取票上传流程、异步发布与错误恢复 |
| `references/assets-generation.md` | 封面、简谱、配乐的生成方法与排版坑 |
| `references/writing-and-humanizer.md` | 推文结构、钩子写法、去 AI 味 31 条检查点、事实核对 |
| `scripts/upload_images.py` | 批量取票上传图片，输出 `file_path` 映射（仅标准库） |
| `scripts/prep_images.py` | 封面裁切、去水印、裁白边、压缩、体积检查 |
| `assets/article_template.md` | 推文文案骨架模板 |
| `assets/jianpu_renderer.py`、`crop_white.py`、`make_audio.py` | 简谱与配乐的可改模板 |
| `assets/sample_article.md` | 通过去 AI 味核对的成稿范例 |

## 安装

把整个目录放到用户级 skills 目录：

- Windows：`C:\Users\<用户名>\.workbuddy\skills\wechat-post-builder\`
- macOS / Linux：`~/.workbuddy/skills/wechat-post-builder/`

技能列表在会话启动时加载，放好后新开一个对话即可触发。触发语句示例：

- 「整理成待发布的公众号推文」
- 「把这篇图文发到公众号草稿箱」
- 「做个吸睛封面，去掉水印」
- 「把文案去掉 AI 味」

## 前置条件

- WorkBuddy，且言序连接器（yanxu）已连接并授权
- Python 3.10+；图片处理需要 Pillow
- 可选：Edge / Chrome 无头渲染谱面、ffmpeg 转 MP3、图像生成能力做封面

脚本会自动探测隔离环境中的 Pillow，也可用 `WB_PYLIBS` 环境变量指定 Pillow 所在目录。

## 文案规则

文案按 [Humanizer-zh](https://github.com/op7418/Humanizer-zh) 的 31 条检查点去除模板化表达，并做事实核对：不新增原文没有的信息、不把「可能」写成「确定」、逐图讲解要与素材一致。完整清单见 `references/writing-and-humanizer.md`。

## 边界

只写到公众号草稿箱，不群发。音频、音乐播放器、投票、超链接等公众号原生组件无法通过接口写入，需要在后台手动插入。

---

作者 / 维护者：[@jianggong95-netizen](https://github.com/jianggong95-netizen)

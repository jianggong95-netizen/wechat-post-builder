# 言序 API：取票、建稿、发布

本文件是 `yanxu-publisher` 连接器技能的补充，重点记录**图片上传通道**与实测踩坑。发布环节的基本规范仍以 `yanxu-publisher` 为准。

## 0. 调用方式

言序工具是 deferred 工具：先用 `ToolSearch` 以 `tool_names` 加载 schema，再用 `DeferExecuteTool` 调用。常用工具名：

```
mcp__yanxu__list_wechat_accounts
mcp__yanxu__list_theme_styles
mcp__yanxu__get_upload_channel
mcp__yanxu__create_article
mcp__yanxu__publish_article
```

一次 `ToolSearch` 可同时加载多个。

## 1. 账号与主题

- `list_wechat_accounts`（无参数）→ `account_id`、`default_theme_id`、公众号名称。
- `list_theme_styles`（无参数）→ `theme_id` 与样式名称。用户说「曜金质感」这类名称时，先映射成 `theme_id`。
- 所有 ID 只用本次会话的工具返回值，不要用历史会话或本文件里的示例 ID。

## 2. 图片上传通道（最容易出错的一步）

### 为什么必须走这一步

`create_article` 的 `image.url` / `cover_img` 只接受**服务端可访问的 http(s) URL 或服务端本地相对路径**。把 `D:\...\page1.png` 这类本机路径写进去，工具不会报错，但生成出的文章**没有图片**。这是实测遇到的第一个失败：文章建好了，图全丢。

### get_upload_channel

| 参数 | 取值 | 说明 |
|---|---|---|
| `scene` | `body` | 正文配图，落 `mcp/`，**7 天过期**，单张 ≤1MB |
| | `cover` | 封面，落 `cover/`，不过期，≤2MB |
| | `frame` | 挂件图，落 `frame/`，不过期，≤2MB |

返回 `upload_url`，形如 `{APP_DOMAIN}/api/once/upload?ticket=<uuid>`，**5 分钟内有效，且一次性**。

### 上传请求

用 multipart/form-data POST 到 `upload_url`，文件字段名为 `file`（或 `img`）。成功后返回 `url`（公网直链）与 `file_path`（相对路径）。**建稿时优先使用 `file_path`**。

Python 标准库实现（环境无 `requests` 时可用，无第三方依赖）：

```python
import urllib.request, os

def upload(upload_url, path, field="file"):
    data = open(path, "rb").read()
    b = "----b" + os.urandom(8).hex()
    name = os.path.basename(path)
    body = (
        f'--{b}\r\nContent-Disposition: form-data; name="{field}"; '
        f'filename="{name}"\r\nContent-Type: image/png\r\n\r\n'
    ).encode() + data + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(
        upload_url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={b}"},
    )
    return urllib.request.urlopen(req).read().decode()
```

等价的 curl：`curl -s -X POST "<upload_url>" -F "file=@page1.png"`

### 批量流程

1. 统计需要上传的图片数量 N（正文图用 `scene=body`，封面用 `scene=cover`）。
2. **调 N 次** `get_upload_channel`，把返回的 `upload_url` 按图片顺序逐行写入 `tickets.txt`。不要复用同一 ticket，也不要试图在脚本里直接调 MCP 接口取票。
3. 立刻运行 `scripts/upload_images.py`，传 `--tickets tickets.txt` 与图片路径列表。
4. 记录输出的 `file_path` 映射，用于 payload。
5. 取票到上传间隔控制在 5 分钟内；票过期就重新取。

失败常见原因：ticket 复用、超过 5 分钟、文件超过对应 scene 的体积上限、网络中断。

## 3. create_article

必填 `title`、`intro`、`chapters`；可选 `abstract`、`cover_img`。顶层是**扁平结构**，`intro` / `chapters` 与 `title` 同级，不要套 `content` 包裹。

| 字段 | 约束 |
|---|---|
| `title` | ≤30 字，超限被拒 |
| `abstract` | ≤100 字，写有信息量的摘要，不写「本文介绍了……」 |
| `intro` | 导语，无字数限制 |
| `cover_img` | 封面 `file_path` 或 http(s) URL，可空；空时回落到公众号默认封面、系统封面 |
| `chapters` | 非空数组，或同结构的 JSON 数组字符串；不支持章节嵌套 |

章节结构：`{"type":"chapter","title":"...","blocks":[...]}`。`intro` 与章节 `title` 会被自动渲染，**不要再把它们写成 block**，否则出现两层标题。

块类型只有 4 种：

| type | 字段 |
|---|---|
| `paragraph` | `content`（纯文本，用 `\n` 分段；不要塞 HTML 标签） |
| `image` | `url`、`alt`（可选）；单张 ≤1MB |
| `list` | `style` = `unordered` / `ordered`，`items` = 字符串数组 |
| `table` | `headers` = 字符串数组，`rows` = 二维数组 |

公众号对表格渲染不佳，结构化对比优先改写成段落叙述。

### 图片体积硬约束

- 封面 ≤2MB，正文图单张 ≤1MB。
- 推荐：正文图压到 200–800KB、长边 ≤1200px；封面压到 1MB 以内。
- 优先 JPEG / WebP；PNG 仅用于需要透明底的场景。
- 生成图片后**先检查体积再建稿**，超限先压缩，不要原样提交。

### 音频边界

正文块里没有 audio / music 类型，公众号音乐播放器也无法通过接口写入。处理方式：

1. 本地生成 mp3 交付给用户；
2. 正文最后一节写「文末这段音频，先听两遍」之类的说明；
3. 在该节末尾留一行括号排版提示，例如「（排版提示：请在文末『插入 → 音频』上传随文 mp3，或搜索曲名插入音乐，插入后删除本段括号内容。）」；
4. 交付时明确告诉用户这一步必须后台手动做。

## 4. publish_article

| 参数 | 说明 |
|---|---|
| `info_id` | 必填，`create_article` 返回的 `yx50…` |
| `account_id` | 可选；多公众号时必填 |
| `theme_id` | 可选；账号无默认样式时必填 |
| `append_profile` | 可选 `0`/`1`，是否在文末带公众号名片；不传则读账号开关 |

**异步发布**：正文图片 >2 张时返回 `async=true`、`status=0 (pending)`、`media_id` 为空，这是正常受理状态，不是失败。稍后到公众号后台草稿箱或发布记录确认 `status=1`（成功）/ `status=2`（失败）。`image_count` 字段可用来核对图片是否被正确识别。

**流程约束**：建稿后默认先复述标题 + `info_id` + 公众号名 + 主题名，等用户确认再发布。用户明确说「写完直接发到草稿箱」时可跳过复述；说「先建稿 / 待发布 / 给我看看」时只做到建稿，停在 `info_id`。

## 5. 错误恢复

| 现象 | 处理 |
|---|---|
| 建稿成功但草稿箱无图 | 检查 `image.url` 是否为本地路径；重新取票上传，用新 `file_path` 重建稿件 |
| 上传返回 ticket 无效 / 过期 | 重新 `get_upload_channel`，5 分钟内完成上传 |
| 图片超体积导致建稿失败 | 压缩后重生成 payload，不原样重发 |
| `title` / `abstract` 超限 | 截断或改写后重试 |
| 多账号未指定 `account_id` | 先 `list_wechat_accounts`，让用户选 |
| `info_id` 不存在 | 确认来自本次 `create_article`，不要凭记忆编造 |
| 401 / 授权失效 | 引导用户在连接器页重新连接授权 |
| 异步发布后长时间未见草稿 | 查发布记录；必要时用同一 payload 重新建稿并发布 |

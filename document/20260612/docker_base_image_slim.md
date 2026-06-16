# 基础镜像瘦身（第一步，零功能损失）

日期：2026-06-12

## 背景

talebook 镜像（arm64 实测 2.63GB）体积过大。起因是评估「能否把 `ebook-convert`
编译成静态工具来缩小镜像」。结论：不可行——`ebook-convert` 是 Python 程序，转换
依赖 Qt6 Gui（封面/图片走 QImage），PDF 输出依赖 QtWebEngine（无头 Chromium），
均无静态链接形态；calibre 官方二进制同样 GB 级；且 webserver 有 17 处直接
`import calibre`，无法解耦。

但镜像本身有大量与装法相关的浪费空间，本次先做不影响任何功能的第一步。
（后续的 slim 变体——以放弃 PDF 输出换取进一步瘦身——单独提交。）

## 本次改动（第一阶段：只准备 base 8.6）

1. **全程 `--no-install-recommends`**：apt 的 Recommends 会拖进
   scipy / matplotlib / GPU 驱动 / gcc / vim 等数百 MB 与运行无关的包。
2. **移除遗留的 `python3-pyqt5*` 系列**：Debian 13 的 calibre 已改用 Qt6 / PyQt6，
   原先显式安装的 `python3-pyqt5`、`python3-pyqt5.qtwebengine` 等是 Debian 12
   时代的遗留——等于在 Qt6 之外又重复安装了一整套 Qt5 / Chromium（含
   `libQt5WebEngineCore` 约 123MB）。验证逻辑同步从 PyQt5 改为 PyQt6。
3. **显式保留 `build-essential` / `python3-dev`**：原先由 `python3-pip` 的
   Recommends 隐式带入；主 Dockerfile 中 pip 安装 `requirements.txt` 时部分包
   （如 `quickjs`）无预编译 wheel 需源码编译，故显式保留，避免 no-recommends 后构建失败。
4. **显式保留 Qt6 图片插件**：`qt6-image-formats-plugins` / `qt6-svg-plugins`
   是 calibre-bin 的 Recommends；改用 no-recommends 后需要显式保留，避免 EPUB/HTML
   内容或封面中的 WEBP/TIFF/SVG 图片支持退化。
5. **补装 `fonts-wqy-microhei`**：`services/convert.py` 转 PDF 时硬编码了文泉驿
   微米黑字体，但此前镜像并未安装该字体（中文 PDF 排版会退化为 fallback 字体），此处补上。
6. Makefile 的 `push-base` 改用 buildx 多架构发布 `linux/amd64,linux/arm64,linux/arm/v7`。

主 `Dockerfile` 本阶段仍保留 `talebook/talebook-base:8.5`，避免在 `8.6` tag
尚未发布前让主镜像 CI 直接依赖不存在的基础镜像。待 `base-v8.6.0` 发布完成后，
第二阶段再切换主镜像到 `8.6` 并引入 slim 变体。

## 实测效果（arm64，拉取/存储体积）

下表为 base 8.6 构建结果，以及后续第二阶段切换主镜像到 8.6 后的完整镜像结果。

| 镜像 | 改造前 | 改造后 | 变化 |
|---|---|---|---|
| base（talebook-base） | ~2.5GB | 1.79GB | -28% |
| 完整版（production-spa） | 2.63GB | 1.98GB | -25%，**零功能损失** |

base 8.6 已本地验证：六条转换链（txt/epub/mobi/azw3 互转）+ PDF 输出均正常。

## 发布注意

base 8.6 需先发布为多架构 tag：合并后推 `base-v8.6.0` tag 触发
build-base workflow（推荐），或在配置好 buildx 的环境中执行 `make push-base`。
确认 `talebook/talebook-base:8.6` 可拉取后，再合入第二阶段 PR 切换主镜像。

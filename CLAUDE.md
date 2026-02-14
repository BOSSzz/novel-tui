# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

novel-tui 是一个基于 Textual 框架的终端小说阅读器（TUI），支持 .txt 文件的导入、章节解析、阅读和全文搜索。UI 文本为中文。

## Commands

```bash
# 安装依赖
uv sync

# 运行应用
uv run novel-tui
# 或
uv run python -m novel_tui

# 运行全部测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/test_parser.py

# 运行单个测试函数
uv run pytest tests/test_parser.py::test_parse_chapters -v
```

## Architecture

采用 src layout（`src/novel_tui/`），使用 hatchling 构建，Python 3.12+。

### 层次结构

- **app.py** — Textual `App` 入口，加载 TCSS 样式，启动时 push `BookListScreen`
- **screens/** — 屏幕层：`BookListScreen`（书架）→ `AddBookModal`（添加书籍）→ `ReadingScreen`（阅读）
- **widgets/** — 自定义 Textual 组件：`BookTable`、`ContentView`（自定义逻辑行滚动）、`ChapterSidebar`、`SearchBar`、`StatusBar`、`FilePicker`
- **core/** — 业务逻辑：`parser.py`（章节解析+编码检测）、`reader.py`（字节偏移读取）、`search.py`（全文搜索）
- **db/** — 数据层：`connection.py`（SQLite 单例连接）、`models.py`（dataclass 模型）、`repository.py`（CRUD 函数）
- **styles/** — Textual CSS 文件（colors.tcss, app.tcss, book_list.tcss, reading.tcss）

### 关键设计

- **章节定位用字节偏移**：`parser.py` 解析时计算每个章节的 `byte_offset` 和 `length`，`reader.py` 通过 `seek()` 直接读取，避免加载整个文件
- **章节检测**：使用正则匹配中文章节标题（`第X章`/`第X卷`），限制行长 `.{0,50}` 排除正文中的误匹配；无章节时按 500 行切分
- **编码检测**：按序尝试 utf-8 → gb18030 → gbk → big5，取 32KB 样本
- **Widget 间通信**：使用 Textual Message 机制（如 `ChapterSidebar.ChapterSelected`、`SearchBar.SearchRequested`），Screen 层监听并协调
- **ContentView 自定义滚动**：不使用 Textual 内置滚动，自行维护 `_top_line` 索引实现逻辑行滚动和自动换行
- **后台任务**：搜索和书籍解析通过 `@work(thread=True)` 在后台线程执行，通过 `call_from_thread` 回调主线程
- **数据库**：SQLite + WAL 模式，单例连接，数据存储在 `platformdirs.user_data_dir("novel-tui")`

### 测试

测试使用 pytest，位于 `tests/`。数据库测试通过 `_fresh_db` fixture 使用临时数据库（`reset_connection()` + `get_connection(tmp_path)`）。解析器测试通过 `tempfile` 创建临时 .txt 文件。

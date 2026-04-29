# OKX Paper Trading Web Dashboard

本项目是一个本地只读 Web Dashboard，用于查看 paper trading 系统的运行状态、权益曲线、交易记录、日志和文件健康状态。

## 功能概览

- 账户摘要：Balance、Equity、Unrealized、Last Close
- 交易统计：OPEN / ADD / CLOSE 数量、Closed PnL、手续费
- 图表：Equity 曲线、BTC Close 复盘曲线、OPEN / ADD / CLOSE 标记
- 表格/卡片：最近交易记录、ADD 记录
- 当前状态：持仓、风险、止损距离、ATR / ADX / Signal
- 文件健康：关键数据文件是否存在、大小、更新时间
- 日志查看：最近日志行并高亮关键事件
- 桌面端和手机端自适应展示

## 安全边界

本项目只做展示，不提供任何交易操作能力。

- 不下单
- 不平仓
- 不修改策略参数
- 不触发回测
- 不写入交易状态文件或交易记录文件
- 不导入交易主程序

## 运行要求

需要 Python 环境，并安装以下依赖：

```bash
fastapi
uvicorn
pandas
```

如果当前环境缺少依赖，可执行：

```bash
pip install -r requirements.txt
```

## 前台启动

在项目目录执行：

```bash
cd /path/to/okex_web
./run.sh
```

默认监听：

```text
0.0.0.0:8008
```

本机访问：

```text
http://127.0.0.1:8008
```

局域网访问：

```text
http://服务器IP:8008
```

## 后台启动

使用 `nohup` 后台运行：

```bash
cd /path/to/okex_web && nohup ./run.sh > okex_web.log 2>&1 &
```

查看是否运行：

```bash
ps -ef | grep '[u]vicorn app:app'
```

查看服务日志：

```bash
tail -f /path/to/okex_web/okex_web.log
```

停止服务：

```bash
pkill -f 'uvicorn app:app'
```

如果启动时报端口占用，通常说明已有旧服务在运行，可先停止后再启动。

## API 简介

常用接口：

```text
GET /api/status
GET /api/trades?limit=50
GET /api/adds?limit=30
GET /api/equity?limit=500
GET /api/candles?limit=300
GET /api/logs?limit=200
GET /chart.png
```

简单测试：

```bash
curl http://127.0.0.1:8008/api/status | python3 -m json.tool
```

## 手机端显示

页面会自动适配手机屏幕。也可以手动强制使用手机布局：

```text
http://服务器IP:8008/?mobile=1
```

页面右下角也有 `Mobile View` 按钮，可手动切换显示模式。

## 常见问题

### 1. 访问不了局域网地址

确认服务正在运行，并确认防火墙允许 8008 端口。

### 2. 页面图表不显示

当前 ECharts 从 CDN 加载。如果浏览器无法访问外网，图表库可能加载失败。后续可以把 ECharts 下载到本地 `static/vendor/` 后再引用。

### 3. 终端出现 Invalid HTTP request

通常是浏览器、手机或局域网设备对 HTTP 服务做了探测，或者误用 `https://` 访问了 HTTP 端口。请确认使用：

```text
http://服务器IP:8008
```

### 4. 修改前端后手机仍看到旧样式

尝试刷新页面、清理浏览器缓存，或在 URL 后加查询参数，例如：

```text
http://服务器IP:8008/?v=refresh
```

## 文件说明

```text
app.py              FastAPI 入口和 API 路由
config.py           路径配置和展示参数
data_reader.py      只读数据读取、清洗和统计逻辑
run.sh              启动脚本
requirements.txt    Python 依赖
static/index.html   页面结构
static/app.js       前端数据请求和图表渲染
static/style.css    页面样式和响应式布局
```

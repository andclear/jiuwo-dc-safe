# Jiuwo Discord Safe Bot

一个基于 Discord 论坛频道的资源安全分发 Bot，采用"无数据库"架构设计。

## 📝 致谢

本Bot受到 `Discord 旅程`频道发布作品Bot的启发，在此表示感谢。

## ✨ 特性

- 📦 **资源发布** - 支持上传最多 5 个文件，自定义版权规则和下载门槛
- 📥 **安全下载** - 支持自由下载、互动验证、提取码三种模式
- 🔄 **原地更新** - 更新文件时保持 Embed 在原位置
- 🔒 **权限控制** - 仅发布者可管理自己的作品
- 🗄️ **无数据库** - 所有数据存储在 Discord，部署简单可靠
- 📒 **频道白名单** - 限制 Bot 命令的使用范围

## 📋 命令列表

| 命令 | 描述 |
|-----|------|
| `/发布作品` | 在论坛帖子中发布资源 |
| `/获取作品` | 获取当前帖子的下载链接 |
| `/更新作品` | 上传新文件覆盖旧作品 |

## 🚀 部署

### 1. 配置环境变量

复制并编辑 `.env` 文件：

```bash
cp .env.example .env
```

```env
BOT_TOKEN=你的Bot令牌
WAREHOUSE_CHANNEL_ID=仓库频道ID
```

### 2. 配置频道白名单（可选）

编辑 `channels.txt`，每行一个频道 ID：

```
# 允许使用 Bot 的论坛频道
123456789012345678
987654321098765432
```

如果不配置频道白名单，或配置为空，或将内容全部注释，Bot 将允许所有论坛频道使用 Bot 命令。

### 3. Docker 部署

```bash
docker-compose up -d --build
```

### 4. 查看日志

```bash
docker-compose logs -f
```

## 🔧 故障排查

### 命令不显示

```bash
# 清除所有命令缓存
docker-compose run --rm discord-bot python scripts/clear_commands.py

# 重新部署
docker-compose up -d --build
```

### 重新加载频道白名单

修改 `channels.txt` 后重启容器：

```bash
docker-compose restart
```

## 📁 项目结构

```
├── bot.py              # Bot 核心类
├── main.py             # 入口文件
├── config.py           # 配置加载
├── channels.txt        # 频道白名单
├── cogs/
│   ├── publish.py      # 发布作品模块
│   ├── download.py     # 获取作品模块
│   └── manage.py       # 管理功能模块
├── utils/
│   ├── metadata.py     # 元数据处理
│   └── embed_builder.py # Embed 构建器
├── scripts/
│   └── clear_commands.py # 命令清除工具
├── Dockerfile
└── docker-compose.yml
```

## 📜 许可证

MIT License

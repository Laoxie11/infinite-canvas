# 创新创业AI平台

创新创业AI平台面向创新创业中心师生团队，提供项目画布、AI 生图、AI 视频、案例提示词和项目素材沉淀能力，帮助团队把创意、参考图、提示词和生成结果组织到同一个工作台中持续推演。

## 核心功能

- 项目画布：创建多个项目画布，支持节点拖拽缩放、连线、小地图、撤销重做、导入导出。
- AI 创作：支持 OpenAI 兼容接口的文生图、图生图、参考图编辑、视频生成和文本问答。
- 画布助手：围绕选中节点和上游节点对话、生图，并把结果插回画布。
- 案例提示词：沉淀可复用提示词、参考风格和案例图片。
- 项目素材：保存项目中的文本、图片和视频素材，便于后续复用。

## 部署

推荐在服务器上通过 Docker Compose 部署。

```bash
git clone https://github.com/Laoxie11/infinite-canvas.git
cd infinite-canvas
cp .env.example .env
```

编辑 `.env`，至少修改：

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=请改成强密码
JWT_SECRET=请改成长随机字符串
STORAGE_DRIVER=sqlite
DATABASE_DSN=data/infinite-canvas.db
```

启动服务：

```bash
docker compose up -d
```

如果服务器拉取镜像较慢或失败，可以本地构建：

```bash
docker compose -f docker-compose.local.yml up -d --build
```

默认访问地址：

```text
http://服务器IP:3000
```

后台地址：

```text
http://服务器IP:3000/admin
```

## 模型渠道

后台登录后，在系统设置中配置 OpenAI 兼容渠道。以 foxcode 中转站为例：

```text
名称：foxcode
Base URL：https://dm-fox.rjj.cc/codex
API Key：sk-xxxx
模型列表：gpt-image-2
启用：开启
协议：openai
```

前台建议使用云端渠道，由后端代理模型请求，避免浏览器 CORS 和 API Key 暴露问题。

## 数据说明

- 默认使用 SQLite，数据文件位于 `data/infinite-canvas.db`。
- Docker 部署时 `./data` 会挂载到容器内 `/app/data`，请勿删除服务器上的 `data` 目录。
- 项目画布和项目素材目前主要保存在浏览器本地，不会随账号自动云同步。
- AI API Key 保存在后台渠道配置中，由后端代理请求上游接口。

## 常用命令

查看日志：

```bash
docker compose logs -f
```

更新代码：

```bash
git pull
docker compose up -d
```

本地构建更新：

```bash
git pull
docker compose -f docker-compose.local.yml up -d --build
```

停止服务：

```bash
docker compose down
```

## 文档

- [功能介绍](docs/features.md)
- [部署说明](docs/deployment.md)
- [画布节点操作手册](docs/canvas-node-manual.md)
- [画布快捷键](docs/canvas-shortcuts.md)
- [后台数据库说明](docs/backend-database.md)
- [系统配置数据结构](docs/system-settings.md)
- [接口响应约定](docs/api-response.md)

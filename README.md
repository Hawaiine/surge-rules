# 🌊 Surge Rules

> 品牌分流规则集，为 Surge 客户端提供完整的品牌级流量分流方案。每日自动更新。

[![Daily Sync](https://github.com/Hawaiine/surge-rules/actions/workflows/daily-sync.yml/badge.svg)](https://github.com/Hawaiine/surge-rules/actions/workflows/daily-sync.yml)
[![License](https://img.shields.io/github/license/Hawaiine/surge-rules)](LICENSE)
[![Rulesets](https://img.shields.io/badge/rulesets-107-blue)](#-规则集列表)
[![Total Rules](https://img.shields.io/badge/total_rules-325K-brightgreen)](#-规则集列表)

---

## ✨ 特性

- **107 个品牌规则集** — 覆盖主流流媒体、社交、AI、游戏、云服务等
- **21 个地区节点组** — 香港、日本、美国、新加坡、台湾、韩国、欧洲、南美等
- **双版本配置** — `Surge.conf`（完整注释版）+ `Surge.min.conf`（精简紧凑版）
- **每日自动同步** — UTC 22:00 自动拉取最新规则，推送到 Discord 通知
- **幂等转换** — 无变化不提交，不更新时间戳
- **规则校验** — 每轮同步自动校验规则集头部与 payload 一致性

## 📁 目录结构

```
surge-rules/
├── ruleset/                    # Surge .list 规则集（每品牌独立目录）
│   ├── Netflix/
│   │   ├── Netflix.list        # 规则内容
│   │   └── README.md           # 品牌统计信息
│   ├── Apple/
│   └── ...
├── configs/
│   ├── Surge.conf              # 完整配置（含注释、段间空行）
│   └── Surge.min.conf          # 精简配置（无注释、紧凑排列）
├── scripts/                    # 转换与校验脚本
│   ├── batch_update.py         # 日更入口
│   ├── fetch_upstream.py       # 上游拉取
│   ├── parse_ruleset.py        # 规则格式转换
│   ├── generate_config.py      # Surge 配置生成
│   ├── verify_rulesets.py      # 规则集一致性校验
│   └── update_readmes.py       # README 自动生成
└── .github/workflows/
    └── daily-sync.yml          # 每日自动同步 CI
```

## 🚀 使用方式

### 快速开始

1. 打开 Surge → 配置文件 → 编辑
2. 将 `configs/Surge.conf` 内容粘贴进去
3. 替换 `[Proxy]` 中的示例节点为实际代理节点
4. 保存并连接

### 自定义设置

- **精简版**：使用 `Surge.min.conf` 替代完整版，去除所有注释，更紧凑
- **品牌规则开关**：在 `[Rule]` 段中，注释/取消注释对应品牌的 `RULE-SET` 行即可启用/禁用
- **节点替换**：`[Proxy]` 段中的 `ProxyA`、`ProxyB` 为示例，替换为你的实际代理

## 📊 规则集列表

| 规则集 | 分类 | 规则集 | 分类 |
|--------|------|--------|------|
| Apple | 🍎 苹果生态 | Netflix | 🎬 流媒体 |
| Google | 🔍 搜索引擎 | OpenAI | 🤖 人工智能 |
| Microsoft | 🪟 微软生态 | YouTube | 🎥 视频平台 |
| Amazon | 🛒 电商云服务 | Disney | 🎬 流媒体 |
| Telegram | 💬 即时通讯 | Discord | 💬 即时通讯 |
| Facebook | 📱 社交平台 | Instagram | 📱 社交平台 |
| TikTok | 📱 短视频 | Twitter/X | 📱 社交平台 |
| GitHub | 💻 开发者工具 | Cloudflare | 🌐 CDN 安全 |
| Spotify | 🎵 音乐平台 | Steam | 🎮 游戏平台 |
| Nintendo | 🎮 游戏主机 | PlayStation | 🎮 游戏主机 |
| Bilibili | 📺 视频平台 | Pixiv | 🎨 插画社区 |
| Netflix | 🎬 流媒体 | OpenAI | 🤖 人工智能 |
| ... | | | |

> 共 **107** 个规则集，**325,827** 条规则。

## 🎨 品牌图标

图标来自 [Oasisic-Icons](https://github.com/Hawaiine/Oasisic-Icons)，为每个品牌提供对应的识别图标。

## 🔄 自动更新

项目通过 GitHub Actions 每日自动同步（UTC 22:00 / 北京时间 06:00），更新完成后推送至 `#🔄・surge规则更新` 频道通知。

## 📚 参考资料

- [Surge 官方文档](https://manual.nssurge.com/)
- [Surge RULE-SET 文档](https://manual.nssurge.com/rule/ruleset.html)
- [Oasisic-Icons](https://github.com/Hawaiine/Oasisic-Icons)

## 📄 许可

[MIT](LICENSE)
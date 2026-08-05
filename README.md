# 🌊 Surge Rules

> 从 [Hawaiine/mihomo-rules](https://github.com/Hawaiine/mihomo-rules) 自动转换的 **Surge** 规则集，每日同步。

[CI](https://github.com/Hawaiine/surge-rules/actions/workflows/daily-sync.yml)
[上游](https://github.com/Hawaiine/mihomo-rules)
[图标源](https://github.com/Hawaiine/Oasisic-Icons)

## 📁 目录结构

```
surge-rules/
├── ruleset/                    # Surge .list 规则集
├── configs/Surge/
│   ├── Surge.conf              # 完整配置（注释版）
│   └── Surge.min.conf          # 精简配置（无注释）
├── scripts/                    # 转换与校验脚本
└── .github/workflows/
    └── daily-sync.yml          # 每日自动同步
```

## 🚀 使用方式

1. 打开 Surge → 配置文件 → 编辑
2. 将 `configs/Surge/Surge.conf` 内容粘贴进去
3. 替换 `[Proxy]` 中的示例节点为实际代理节点
4. 保存并连接

## 📊 规则集列表

| 规则集 | 数量 | 规则集 | 数量 |
|--------|------|--------|------|
| Apple | 1477 | Netflix | 39 |
| Direct | 112127 | OpenAI | 45 |
| Reject | 167745 | ... | ... |

> 共 **107** 个规则集，**325,400** 条规则。

## 🎨 品牌图标

图标来自 [Oasisic-Icons](https://github.com/Hawaiine/Oasisic-Icons)。

## 📚 参考资料

- [Surge 官方文档](https://manual.nssurge.com/)
- [Surge RULE-SET 文档](https://manual.nssurge.com/rule/ruleset.html)
- [mihomo-rules 上游](https://github.com/Hawaiine/mihomo-rules)

#!/usr/bin/env python3
"""
batch_update.py — 日更入口
流程：
1. fetch_upstream：从 mihomo-rules 拉取/更新本地上游缓存
2. parse_ruleset：转换 YAML -> ruleset/*.list
3. generate_config：生成 Surge.conf / Surge.min.conf
4. verify_rulesets：校验 .list 一致性
任一阶段失败则 exit 1。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))


def step_fetch() -> int:
    from fetch_upstream import fetch_all
    cache_root = ROOT / '.cache'
    upstream_dir = cache_root / 'upstream_ruleset'
    upstream_dir.mkdir(parents=True, exist_ok=True)
    # 先从本地缓存收集已有品牌，避免每次全量重建
    brands = sorted([d.name for d in upstream_dir.iterdir() if d.is_dir()])
    if not brands:
        print('[fetch] 本地无上游缓存，需要先初始化品牌列表')
        return 0
    fetched = fetch_all(cache_root, brands)
    print(f'[fetch] 完成: {len(fetched)}/{len(brands)} 个品牌')
    return 0


def step_convert() -> int:
    from parse_ruleset import convert_yaml_to_list
    upstream_dir = ROOT / '.cache' / 'upstream_ruleset'
    if not upstream_dir.exists():
        print('[convert] 无上游缓存，跳过')
        return 0
    brands = sorted([d.name for d in upstream_dir.iterdir() if d.is_dir()])
    updated = 0
    for brand in brands:
        yaml_path = upstream_dir / brand / f'{brand}.yaml'
        # 对齐上游目录结构：ruleset/<Brand>/<Brand>.list
        out_dir = ROOT / 'ruleset' / brand
        out_path = out_dir / f'{brand}.list'
        changed, msg, err = convert_yaml_to_list(yaml_path, brand, out_path)
        if err:
            print(f'[convert] {brand}: {err}')
            continue
        status = 'updated' if changed else 'unchanged'
        print(f'[convert] {brand}: {status} ({msg})')
        if changed:
            updated += 1
    print(f'[convert] 总计更新 {updated} 个文件')
    return 0


def step_generate() -> int:
    from generate_config import main as gen_main
    gen_main()
    return 0


def step_verify() -> int:
    from verify_rulesets import main as verify_main
    return verify_main()


def main() -> int:
    print('=== batch_update.py ===')
    steps = [('fetch', step_fetch), ('convert', step_convert), ('generate', step_generate), ('verify', step_verify)]
    for name, fn in steps:
        print(f'\n[+] step: {name}')
        rc = fn()
        if rc != 0:
            print(f'[-] {name} failed, exit {rc}')
            return rc
    print('\n=== 完成 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())

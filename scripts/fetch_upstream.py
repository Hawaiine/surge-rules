#!/usr/bin/env python3
"""
fetch_upstream.py — 从 Hawaiine/mihomo-rules 拉取规则集到本地 upstream_cache/
不写 ruleset/，仅提供上游 YAML 文件供后续 convert 使用。
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Optional

try:
    from lib.icons_map import IconsMap
except Exception:
    IconsMap = None  # type: ignore

RAW_BASE = 'https://raw.githubusercontent.com/Hawaiine/mihomo-rules/main'
RULESET_PATH = 'ruleset'


def upstream_ruleset_dir(cache_root: Path) -> Path:
    return cache_root / 'upstream_ruleset'


def fetch_brand(cache_root: Path, brand: str, github_token: Optional[str] = None) -> Optional[Path]:
    yaml_rel = f'{RULESET_PATH}/{brand}/{brand}.yaml'
    url = f'{RAW_BASE}/{yaml_rel}'
    target_dir = upstream_ruleset_dir(cache_root) / brand
    target = target_dir / f'{brand}.yaml'
    if target.exists():
        return target
    target_dir.mkdir(parents=True, exist_ok=True)
    return None


def fetch_all(cache_root: Path, brands: List[str], github_token: Optional[str] = None) -> List[str]:
    fetched: List[str] = []
    base = upstream_ruleset_dir(cache_root)
    for brand in brands:
        target = base / brand / f'{brand}.yaml'
        if target.exists():
            fetched.append(brand)
            continue
        url = f'{RAW_BASE}/{RULESET_PATH}/{brand}/{brand}.yaml'
        try:
            import urllib.request
            req = urllib.request.Request(url)
            if github_token:
                req.add_header('Authorization', f'token {github_token}')
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            fetched.append(brand)
        except Exception as e:
            print(f'[!] fetch failed: {brand}: {e}')
    return fetched

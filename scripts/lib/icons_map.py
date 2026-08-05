#!/usr/bin/env python3
"""
icons_map.py — Oasisic-Icons 映射
基于本地仓库的 icons/ 目录构建品牌->图标 URL 映射。
图标命名规则优先精确匹配品牌名；其次去掉后缀数字后的基础名匹配。
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional

# 与仓库一致的 raw URL 前缀
GITHUB_ICON = 'https://raw.githubusercontent.com/Hawaiine/Oasisic-Icons/main/icons'


def _base_name(name: str) -> str:
    return re.sub(r'-\d+$', '', name)


class IconsMap:
    def __init__(self, repo_root: Optional[str] = None):
        if repo_root is None:
            repo_root = os.environ.get('OASISIC_ICONS_REPO', '/opt/data/Oasisic-Icons')
        self.repo = Path(repo_root)
        self._map: Dict[str, str] = {}
        self._names: list[str] = []

    def build(self) -> Dict[str, str]:
        icons_dir = self.repo / 'icons'
        if not icons_dir.exists():
            return {}

        # 先遍历 surge-icon.json，它已整理好图标集合
        surge_json = self.repo / 'config' / 'surge-icon.json'
        if surge_json.exists():
            try:
                with open(surge_json) as f:
                    data = json.load(f)
                for item in data.get('icons', []):
                    name = item.get('name')
                    url = item.get('url')
                    if name and url:
                        self._map[name] = url
                        self._names.append(name)
            except Exception:
                pass

        # 再扫描目录补充未在 JSON 中的图标
        for root, dirs, files in os.walk(icons_dir):
            for fname in files:
                if not fname.endswith('.png'):
                    continue
                name = fname.rsplit('.', 1)[0]
                cat = os.path.relpath(root, icons_dir)
                url = f'{GITHUB_ICON}/{cat}/{fname}'
                if name not in self._map:
                    self._map[name] = url
                    self._names.append(name)

        return self._map

    def match(self, brand: str) -> Optional[str]:
        if not self._map:
            self.build()
        # 精确匹配
        if brand in self._map:
            return self._map[brand]
        # 忽略大小写
        lower = brand.lower()
        for name, url in self._map.items():
            if name.lower() == lower:
                return url
        # 去掉尾部数字后基础名匹配
        base = re_sub_digits(lower)
        for name, url in self._map.items():
            if re_sub_digits(name.lower()) == base:
                return url
        return None

    def all_icons(self) -> Dict[str, str]:
        if not self._map:
            self.build()
        return dict(self._map)


def re_sub_digits(name: str) -> str:
    import re
    return re.sub(r'-\d+$', '', name)

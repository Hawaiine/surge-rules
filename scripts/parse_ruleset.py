#!/usr/bin/env python3
"""
parse_ruleset.py — 将 mihomo YAML ruleset 转为 Surge .list
转换规则：
- 跳过 YAML header 注释块
- 从 payload 提取规则
- 仅保留 Surge 支持的规则类型
- 保留 IP-CIDR/IP-CIDR6 的 no-resolve 标记
输出附带 header（计数/时间戳）。
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from lib.canonical import (
    TYPES_ORDER,
    CanonicalRule,
    canonicalize,
    count_by_type,
    parse_rule_line,
    total_rules,
)

HEADER_LINE_RE = re.compile(r'^#\s+(?P<key>[^:]+):\s*(?P<value>.+)$')
PAYLOAD_START_RE = re.compile(r'^\s*payload\s*:')


def parse_yaml_header_and_payload(path: Path) -> Tuple[dict[str, str], List[str]]:
    """返回 (header字段, payload行列表)。"""
    header: dict[str, str] = {}
    payload: List[str] = []
    in_payload = False
    with open(path) as f:
        for raw in f:
            line = raw.rstrip('\n')
            s = line.strip()
            if not in_payload:
                if PAYLOAD_START_RE.match(s):
                    in_payload = True
                    continue
                m = HEADER_LINE_RE.match(s)
                if m:
                    header[m.group('key').strip()] = m.group('value').strip()
                continue
            # in payload
            if not s or s.startswith('#'):
                continue
            payload.append(s)
    return header, payload


def make_header(header: dict[str, str], counts: dict[str, int], total: int) -> str:
    lines = ['# ===========================================']
    lines.append(f'# Rule Name: {header.get("Rule Name", "Ruleset")}')
    lines.append(f'# Updated: {header.get("Updated", "")}')
    for t in TYPES_ORDER:
        if counts.get(t, 0):
            lines.append(f'# {t}: {counts[t]}')
    if total:
        lines.append(f'# TOTAL: {total}')
    lines.append('# ===========================================')
    return '\n'.join(lines) + '\n'


def convert_yaml_to_list(yaml_path: Path, brand: str, out_path: Path) -> Tuple[bool, str, Optional[str]]:
    """转换单个品牌 yaml -> .list；返回 (changed, message, error)。"""
    try:
        header, payload = parse_yaml_header_and_payload(yaml_path)
    except Exception as e:
        return False, brand, f'parse error: {e}'

    kept, dropped_unsupported, dropped_invalid = canonicalize(payload)
    counts = count_by_type(kept)
    total = total_rules(kept)
    content = make_header(header, counts, total) + '\n'.join(r.line for r in kept) + '\n'

    changed = True
    if out_path.exists():
        existing = out_path.read_text()
        if existing == content:
            changed = False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content)
    msg = f'{brand}: total={total}'
    if dropped_unsupported:
        msg += f', unsupported={len(dropped_unsupported)}'
    if dropped_invalid:
        msg += f', invalid={len(dropped_invalid)}'
    return changed, msg, None

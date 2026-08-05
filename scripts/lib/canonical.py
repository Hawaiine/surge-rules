#!/usr/bin/env python3
"""
canonical.py — Surge 规则集标准化
仅处理 Surge .list 文件支持的规则类型与字段清洗。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

# Surge 规则集白名单（仅保留可安全写入 .list 的类型）
SURGE_TYPES = {
    'DOMAIN',
    'DOMAIN-SUFFIX',
    'DOMAIN-KEYWORD',
    'DOMAIN-REGEX',
    'IP-CIDR',
    'IP-CIDR6',
    'IP-ASN',
}

# 输出字段顺序，用于 header 统计展示
TYPES_ORDER = [
    'DOMAIN',
    'DOMAIN-SUFFIX',
    'DOMAIN-KEYWORD',
    'DOMAIN-REGEX',
    'IP-CIDR',
    'IP-CIDR6',
    'IP-ASN',
]

TYPE_RE = re.compile(r'^\s*(?P<type>[A-Z][A-Z0-9_-]+)\s*,\s*(?P<value>.+)\s*$')


@dataclass
class CanonicalRule:
    raw: str
    rtype: str
    value: str
    extras: str = ''
    supported: bool = True
    drop_reason: Optional[str] = None

    @property
    def line(self) -> str:
        if not self.value:
            return self.raw
        if self.extras:
            return f'{self.rtype},{self.value},{self.extras}'
        return f'{self.rtype},{self.value}'


def parse_rule_line(line: str) -> CanonicalRule:
    text = line.strip()
    if not text or text.startswith('#'):
        return CanonicalRule(raw=line, rtype='', value='', supported=False, drop_reason='comment_or_blank')

    # mihomo YAML payload 行通常为 "- TYPE,value" 格式
    if text.startswith('- '):
        text = text[2:].strip()

    m = TYPE_RE.match(text)
    if not m:
        return CanonicalRule(raw=line, rtype='', value='', supported=False, drop_reason='no_type_prefix')

    rtype = m.group('type').upper()
    value = m.group('value').strip()
    extras = ''

    # 保持 no-resolve 标记（仅 IP-CIDR/IP-CIDR6）
    if rtype in {'IP-CIDR', 'IP-CIDR6'} and value.endswith(',no-resolve'):
        parts = value.rsplit(',', 1)
        value = parts[0].strip()
        extras = 'no-resolve'

    if rtype not in SURGE_TYPES:
        return CanonicalRule(raw=line, rtype=rtype, value=value, extras=extras, supported=False, drop_reason='unsupported_type')

    return CanonicalRule(raw=line, rtype=rtype, value=value, extras=extras, supported=True)


def canonicalize(lines: Iterable[str]) -> Tuple[List[CanonicalRule], List[CanonicalRule], List[CanonicalRule]]:
    """返回 (kept, dropped_unsupported, dropped_invalid)。"""
    kept: List[CanonicalRule] = []
    dropped_unsupported: List[CanonicalRule] = []
    dropped_invalid: List[CanonicalRule] = []

    for line in lines:
        rule = parse_rule_line(line)
        if not rule.rtype:
            dropped_invalid.append(rule)
            continue
        if not rule.supported:
            dropped_unsupported.append(rule)
            continue
        kept.append(rule)

    return kept, dropped_unsupported, dropped_invalid


def count_by_type(rules: Iterable[CanonicalRule]) -> dict[str, int]:
    counts = {t: 0 for t in TYPES_ORDER}
    for r in rules:
        if r.rtype in counts:
            counts[r.rtype] += 1
    return counts


def total_rules(rules: Iterable[CanonicalRule]) -> int:
    return sum(1 for r in rules if r.supported)

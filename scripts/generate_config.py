#!/usr/bin/env python3
"""
generate_config.py — 生成 Surge 配置文件（Surge.conf / Surge.min.conf）
从 ruleset/ 扫描品牌，生成完整 Surge 配置。
输出：
- configs/Surge.conf       # 完整版（含注释、段间空行）
- configs/Surge.min.conf   # 精简版（无注释、紧凑）
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

ROOT = Path(__file__).resolve().parent.parent
_MIHOMO_SCRIPTS = ROOT.parent / 'mihomo-rules' / 'scripts'
if str(_MIHOMO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_MIHOMO_SCRIPTS))

try:
    from commit_writer import STRATEGY_GROUP_MAP  # type: ignore
except Exception:
    STRATEGY_GROUP_MAP = {}

try:
    from lib.ownership_map import SUB_PARENT  # type: ignore
except Exception:
    SUB_PARENT = {}

# 直接加载 lib/icons_map.py，避免包名冲突
import importlib.util
_ICONS_MAP_PATH = _SCRIPTS_DIR / "lib" / "icons_map.py"
_icons_spec = importlib.util.spec_from_file_location("icons_map", _ICONS_MAP_PATH)
_icons_mod = importlib.util.module_from_spec(_icons_spec)
_icons_spec.loader.exec_module(_icons_mod)
IconsMap = _icons_mod.IconsMap

# 基础策略组定义（不含品牌组）
SYSTEM_GROUPS_ORDER = [
    '🛑 全球拦截',
    '🎯 全球直连',
    '🔧 手动切换',
    '🐟 漏网之鱼',
]

# 节点组占位（Surge 示例节点，用户需替换）
NODE_GROUPS = [
    '🇭🇰 香港节点',
    '🇯🇵 日本节点',
    '🇺🇸 美国节点',
    '🇸🇬 新加坡节点',
    '🇹🇼 台湾节点',
    '🇰🇷 韩国节点',
    '🇬🇧 英国节点',
    '🇩🇪 德国节点',
    '🇫🇷 法国节点',
    '🇨🇦 加拿大节点',
    '🇦🇺 澳大利亚节点',
    '🇮🇳 印度节点',
    '🇹🇷 土耳其节点',
    '🇦🇷 阿根廷节点',
    '🇧🇷 巴西节点',
    '🇷🇺 俄罗斯节点',
    '🇲🇾 马来西亚节点',
    '🇹🇭 泰国节点',
    '🇻🇳 越南节点',
    '🇵🇭 菲律宾节点',
    '🇮🇩 印尼节点',
]

# 全量品牌（用于生成 Surge 配置，避免遗漏）
COMMON_BRANDS = [
    'AWS',
    'AbemaTV',
    'Amazon',
    'Anthropic',
    'Apple',
    'AppleTV',
    'Applications',
    'Bahamut',
    'Bangumi',
    'Bank',
    'Bilibili',
    'Bluesky',
    'CATCHPLAY',
    'CNCIDR',
    'Cloudflare',
    'Cursor',
    'DAZN',
    'DAnimeStore',
    'DMMTV',
    'Deezer',
    'Direct',
    'Discord',
    'Disney',
    'Docker',
    'F1TV',
    'Facebook',
    'FujiTV',
    'GameJapan',
    'GeneralAI',
    'GitHub',
    'Google',
    'GoogleAI',
    'HBO',
    'HOYTV',
    'HamiVideo',
    'Hotstar',
    'Hulu',
    'Instagram',
    'KKTV',
    'LINETV',
    'LanCIDR',
    'Lemino',
    'LiTV',
    'Manus',
    'Messenger',
    'MetaBrainz',
    'Microsoft',
    'Mora',
    'MusicJapan',
    'Musixmatch',
    'MyVideo',
    'NHK',
    'Netflix',
    'Niconico',
    'Nintendo',
    'NowE',
    'OasisicSelf',
    'OneDrive',
    'OpenAI',
    'PT',
    'PTChina',
    'PayPal',
    'Perplexity',
    'Pinterest',
    'Pixiv',
    'Podcast',
    'Poe',
    'Porn',
    'PornChina',
    'PrimeVideo',
    'Private',
    'Proxy',
    'Qobuz',
    'Radiko',
    'RakutenTV',
    'ReadsJapan',
    'Reddit',
    'Reject',
    'SiriAI',
    'Spotify',
    'Steam',
    'Synology',
    'TMDB',
    'TVer',
    'Telasa',
    'Telegram',
    'Threads',
    'Tidal',
    'TikTok',
    'Tubi',
    'Twitch',
    'UNext',
    'VideoMarket',
    'Viu',
    'WOWOW',
    'WSJ',
    'Wallpaper',
    'WhatsApp',
    'X',
    'YouTube',
    'YouTubeMusic',
    'ZLibrary',
    'friDayvideo',
    'iCloud',
    'iCloudPrivateRelay',
    'karaokeDAM',
    'myTVSuper',
]


def load_brand_info(ruleset_dir: Path) -> List[dict]:
    brand_info = []
    if not ruleset_dir.exists():
        return brand_info
    for d in sorted(ruleset_dir.iterdir()):
        if not d.is_dir():
            continue
        list_path = d / f'{d.name}.list'
        if not list_path.exists():
            continue
        brand_info.append({
            'key': d.name,
            'sg': STRATEGY_GROUP_MAP.get(d.name, d.name),
            'behavior': 'classical',
        })
    return brand_info


def filter_brand_info(brand_info: List[dict]) -> List[dict]:
    """仅保留常用品牌，避免配置膨胀。"""
    common_keys = set(COMMON_BRANDS)
    result = []
    for bi in brand_info:
        if bi['key'] in common_keys:
            result.append(bi)
    return result


def sort_brands(brand_info: List[dict]) -> List[dict]:
    """子品牌排在父品牌前，避免宽泛规则截胡。"""
    if not SUB_PARENT:
        return brand_info

    sub_parents = set(SUB_PARENT.keys())
    parent_brands = set(SUB_PARENT.values())
    # 品牌 key -> 完整信息
    info_map = {bi['key']: bi for bi in brand_info}

    # 递归收集所有子品牌（含嵌套）
    def collect_children(parent: str, seen: set) -> list:
        kids = []
        for child in sorted(SUB_PARENT.keys()):
            if SUB_PARENT[child] == parent and child not in seen:
                seen.add(child)
                grandkids = collect_children(child, seen)
                kids.append(child)
                kids.extend(grandkids)
        return kids

    result = []
    done = set()
    # 先处理有父品牌的子品牌
    for parent in sorted(parent_brands):
        children = collect_children(parent, done)
        for c in children:
            if c in info_map:
                result.append(info_map[c])
                done.add(c)
        if parent in info_map and parent not in done:
            result.append(info_map[parent])
            done.add(parent)

    # 剩余品牌按字母序
    for bi in brand_info:
        if bi['key'] not in done:
            result.append(bi)

    return result


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists():
        existing = path.read_text()
        if existing == content:
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def gen_general() -> str:
    now = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    return f"""# ===========================================
# Surge Configuration
# Generated from mihomo-rules
# Updated: {now} (UTC+8)
#
# 使用方式（二选一）：
#   A. 远程订阅（推荐）：Surge → 配置文件 → 下载配置文件
#      URL: https://raw.githubusercontent.com/Hawaiine/surge-rules/main/configs/Surge.conf
#   B. 手动配置：Surge → 配置文件 → 编辑，粘贴本文件内容
#
# 使用前必做：
#   1. 替换 [Proxy] 段中的示例节点（ProxyA/ProxyB）为实际代理节点
#   2. 如需更精细的 DNS 策略，取消注释 [DNS] 段中的对应项
#   3. 品牌规则在 [Rule] 段中按需启用/禁用
# ===========================================

[General]
# ===========================================
# loglevel — 日志级别
#   notify: 仅显示通知（默认，推荐）
#   verbose: 显示完整日志（调试用，信息量大）
# ===========================================
loglevel = notify

# ===========================================
# DNS 服务器配置
# Surge 向所有列出的 DNS 服务器同时发起查询，取最快返回的结果。
# 多 DNS 并发查询 → 自动选择最快响应 → 实现国内/外 DNS 分流
#
# 配置说明：
#   system: 使用系统默认 DNS（通常是运营商分配的本地 DNS，解析国内域名快）
#   https://doh.pub/dns-query: 腾讯 DNSPod DoH，国内 CDN 节点，解析国内域名延迟低
#   https://dns.alidns.com/dns-query: 阿里云 DNS，国内 CDN 节点，隐私保护较好
#
# 国内 DNS 优先策略：doh.pub 和 alidns 在国内有 CDN 加速，
# 解析国内域名（如 baidu.com、taobao.com）时延迟远低于 8.8.8.8 等国外 DNS。
# 解析国外域名时，Surge 会同时 query 所有 DNS，国外的 DNS 响应速度
# 可能更快（因为国外域名在国外 DNS 可能有缓存），所以自然实现分流效果。
# ===========================================
dns-server = system, https://doh.pub/dns-query, https://dns.alidns.com/dns-query

# ===========================================
# 加密 DNS（可选，注释掉即不启用）
# 如果希望所有 DNS 查询都走加密通道，取消注释下面这行。
# 注意：仅在有海外节点时建议使用，国内加密 DNS 在国内访问可能反而更慢。
# ===========================================
# encrypted-dns-server = https://dns.alidns.com/dns-query

# ===========================================
# 跳过代理的地址段
# 以下地址段/域名不经过 Surge 代理，直接连接。
# 包括：局域网、本地回环、本地域名
# ===========================================
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local

# ===========================================
# iOS 模式（iOS 设备专用，macOS 用户可忽略）
#   bypass-system: 系统应用不走代理
#   bypass-tun: TUN 模式跳过局域网地址
# ===========================================
# iOS
bypass-system = true
bypass-tun = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12

# ===========================================
# macOS 模式（macOS 设备专用，iOS 用户可忽略）
#   interface: 监听地址（0.0.0.0 = 所有接口）
#   port: HTTP 代理端口
#   socks-port: SOCKS5 代理端口
# ===========================================
# macOS
interface = 0.0.0.0
port = 6152
socks-port = 6153

# ===========================================
# 真实 IP 地址（强制保留真实 IP 的域名）
# 以下域名被用于 NAT 类型检测、游戏联机、流媒体地域验证等场景。
# 如果这些域名被代理或 DNS 劫持，可能导致：
#   - 游戏 NAT 类型变为 Strict（严格）
#   - 流媒体（如 Netflix）检测到代理而拒绝播放
#   - 语音通话（如 Discord）连接失败
# ===========================================
always-real-ip = *.srv.nintendo.net, *.stun.playstation.net, ntp.ubuntu.com

# ===========================================
# hijack-dns — DNS 劫持
# 劫持发往指定地址的 DNS 查询，强制走 Surge 的 DNS 客户端。
# 适用于：路由器、游戏机、智能电视等设备强制使用自定义 DNS 的场景。
# 格式：ip:port，多个用逗号分隔
# 示例：hijack-dns = 8.8.8.8:53, 8.8.4.4:53
# 默认不启用，需要时取消注释。
# ===========================================
# hijack-dns = 8.8.8.8:53, 8.8.4.4:53

# ===========================================
# 代理设置
#   external-controller-access: 远程访问控制（格式: 用户名@密码@地址:端口）
#   proxy: 全局 HTTP 代理（可选）
# ===========================================
external-controller-access = surgerules@127.0.0.1:6170
# proxy = http://127.0.0.1:6152

# ===========================================
# IPv6 支持
#   off: 关闭 IPv6
#   auto: 自动检测网络是否支持 IPv6（默认）
#   always: 始终启用 IPv6
# ===========================================
# ipv6 = auto

"""


def gen_proxy_placeholder() -> str:
    return """[Proxy]
# ===========================================
# Proxy 节点（示例占位，请替换为实际节点）
# ===========================================
ProxyA = http, 1.2.3.4, 443
ProxyB = socks5, 5.6.7.8, 1080
Direct = direct

"""


def gen_proxy_groups_full(icons: Dict[str, str], brand_info: List[dict]) -> str:
    lines: List[str] = ['[Proxy Group]']
    for ng in NODE_GROUPS:
        lines.append(f'{ng} = url-test, ProxyA, ProxyB, Direct, interval=600, timeout=5, tolerance=50')
    for sg in SYSTEM_GROUPS_ORDER:
        lines.append(f'{sg} = select, ProxyA, ProxyB, Direct')
    for i, bi in enumerate(brand_info):
        if i > 0:
            lines.append('')
        lines.append(f'{bi["sg"]} = select, Direct, 🇭🇰 香港节点, 🇯🇵 日本节点, 🇺🇸 美国节点, 🇸🇬 新加坡节点')
        if bi['sg'] in icons:
            lines.append(f'    # icon: {icons[bi["sg"]]}')
    return '\n'.join(lines) + '\n\n'


def gen_proxy_groups_min(icons: Dict[str, str], brand_info: List[dict]) -> str:
    lines: List[str] = ['[Proxy Group]']
    for ng in NODE_GROUPS:
        lines.append(f'{ng} = url-test, ProxyA, ProxyB, Direct, interval=600, timeout=5, tolerance=50')
    for sg in SYSTEM_GROUPS_ORDER:
        lines.append(f'{sg} = select, ProxyA, ProxyB, Direct')
    for bi in brand_info:
        lines.append(f'{bi["sg"]} = select, Direct, 🇭🇰 香港节点, 🇯🇵 日本节点, 🇺🇸 美国节点, 🇸🇬 新加坡节点')
    return '\n'.join(lines) + '\n\n'


def gen_rule_set_line(brand_key: str, brand_sg: str, no_resolve: bool = False, extended: bool = False, use_proxy: bool = True) -> str:
    url = f'https://raw.githubusercontent.com/Hawaiine/surge-rules/main/ruleset/{brand_key}.list'
    if brand_key == 'Reject':
        target = '🛑 全球拦截'
    elif brand_key in {'Direct', 'Private', 'LanCIDR'}:
        target = '🎯 全球直连'
    elif brand_key == 'CNCIDR':
        target = '🎯 全球直连'
    elif brand_key == 'Proxy':
        target = '🔧 手动切换'
    else:
        target = brand_sg if use_proxy else '🎯 全球直连'
    parts = [f'RULE-SET,{url},{target}']
    if no_resolve:
        parts.append('no-resolve')
    if extended:
        parts.append('extended-matching')
    return ','.join(parts)


def gen_rules_full(brand_info: List[dict]) -> str:
    lines = ['[Rule]']
    lines.append('# ----- 1. 拦截 (最高优先级) -----')
    lines.append(gen_rule_set_line('Reject', '🛑 全球拦截', use_proxy=False))
    lines.append('')
    lines.append('# ----- 2. 品牌分流 (按需取消注释, 放在国内规则前) -----')
    lines.append('# 顺序说明: 子品牌/重叠品牌排父品牌前, 避免被宽泛规则截胡')
    lines.append('# 例: AppleTV/SiriAI/iCloud 在 Apple 前')
    common_keys = {bi['key'] for bi in filter_brand_info(brand_info)}
    for bi in brand_info:
        rule_line = gen_rule_set_line(bi['key'], bi['sg'], no_resolve=False, extended=False, use_proxy=True)
        if bi['key'] in common_keys:
            lines.append(rule_line)
        else:
            lines.append(f'# {rule_line}')
    lines.append('')
    lines.append('# ----- 3. 局域网 & 直连 -----')
    lines.append(gen_rule_set_line('Direct', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('Private', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('LanCIDR', '🎯 全球直连', use_proxy=False))
    lines.append('')
    lines.append('# ----- 4. 国内 IP (GeoIP 放最后, 兜底国内流量) -----')
    lines.append(gen_rule_set_line('CNCIDR', '🎯 全球直连', no_resolve=True, use_proxy=False))
    lines.append('GEOIP,CN,🎯 全球直连,no-resolve')
    lines.append('')
    lines.append('# ----- 5. 代理 (国际流量) -----')
    lines.append(gen_rule_set_line('Proxy', '🔧 手动切换', use_proxy=True))
    lines.append('')
    lines.append('# ----- 6. 兜底 (必须最后) -----')
    lines.append('MATCH,🐟 漏网之鱼')
    lines.append('')
    return '\n'.join(lines) + '\n'


def gen_rules_min(brand_info: List[dict]) -> str:
    lines = ['[Rule]']
    common_keys = {bi['key'] for bi in filter_brand_info(brand_info)}
    for bi in brand_info:
        if bi['key'] not in common_keys:
            continue
        lines.append(gen_rule_set_line(bi['key'], bi['sg'], no_resolve=False, extended=False, use_proxy=True))
    lines.append(gen_rule_set_line('Reject', '🛑 全球拦截', use_proxy=False))
    lines.append(gen_rule_set_line('Direct', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('Private', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('LanCIDR', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('CNCIDR', '🎯 全球直连', no_resolve=True, use_proxy=False))
    lines.append('GEOIP,CN,🎯 全球直连,no-resolve')
    lines.append(gen_rule_set_line('Proxy', '🔧 手动切换', use_proxy=True))
    lines.append('MATCH,🐟 漏网之鱼')
    return '\n'.join(lines) + '\n'


def assemble_full(general: str, proxies: str, proxy_groups: str, rules: str) -> str:
    return f"""{general}{proxies}{proxy_groups}{rules}[Host]
# 本地 DNS 映射（按需添加）
# 127.0.0.1 localhost

"""


def assemble_min(general: str, proxies: str, proxy_groups: str, rules: str) -> str:
    return f"""{general}{proxies}{proxy_groups}{rules}[Host]
# 本地 DNS 映射（按需添加）
# 127.0.0.1 localhost

"""


def main() -> None:
    ruleset_dir = ROOT / 'ruleset'
    brand_info = load_brand_info(ruleset_dir)
    brand_info = sort_brands(brand_info)

    icons = IconsMap()
    icons.build()

    general = gen_general()
    proxies = gen_proxy_placeholder()
    common_brand_info = filter_brand_info(brand_info)
    common_brand_info = sort_brands(common_brand_info)
    proxy_groups_full = gen_proxy_groups_full(icons.all_icons(), common_brand_info)
    proxy_groups_min = gen_proxy_groups_min(icons.all_icons(), common_brand_info)
    rules_full = gen_rules_full(brand_info)
    rules_min = gen_rules_min(brand_info)

    full = assemble_full(general, proxies, proxy_groups_full, rules_full)
    min_conf = assemble_min(general, proxies, proxy_groups_min, rules_min)

    out_dir = ROOT / 'configs'
    changed_full = write_if_changed(out_dir / 'Surge.conf', full)
    changed_min = write_if_changed(out_dir / 'Surge.min.conf', min_conf)

    print(f'[+] Surge.conf: {"updated" if changed_full else "unchanged"}')
    print(f'[+] Surge.min.conf: {"updated" if changed_min else "unchanged"}')


if __name__ == '__main__':
    main()

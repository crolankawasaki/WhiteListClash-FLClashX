#!/usr/bin/env python3
"""
VLESS Subscription Merger for FLClashX
Maximum geolocation accuracy: 5 services, consensus voting.
"""

import requests
import base64
import json
import hashlib
import ipaddress
import socket
from datetime import datetime
from collections import Counter
import logging
import os
import sys
import re
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

SOURCES = [
    "https://raw.githubusercontent.com/GoldCaviar/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt",
    "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/26.txt"
]

OUTPUT_FILE = "merged_flclash.yaml"
HISTORY_FILE = "servers_history.json"
GEO_CACHE_FILE = "geo_cache.json"

COUNTRY_DATA = {
    'GB': ('🇬🇧', 'United Kingdom'), 'US': ('🇺🇸', 'United States'), 'DE': ('🇩🇪', 'Germany'),
    'FR': ('🇫🇷', 'France'), 'NL': ('🇳🇱', 'Netherlands'), 'CH': ('🇨🇭', 'Switzerland'),
    'SE': ('🇸🇪', 'Sweden'), 'NO': ('🇳🇴', 'Norway'), 'FI': ('🇫🇮', 'Finland'),
    'DK': ('🇩🇰', 'Denmark'), 'CA': ('🇨🇦', 'Canada'), 'AU': ('🇦🇺', 'Australia'),
    'JP': ('🇯🇵', 'Japan'), 'KR': ('🇰🇷', 'South Korea'), 'SG': ('🇸🇬', 'Singapore'),
    'HK': ('🇭🇰', 'Hong Kong'), 'TW': ('🇹🇼', 'Taiwan'), 'CN': ('🇨🇳', 'China'),
    'IN': ('🇮🇳', 'India'), 'BR': ('🇧🇷', 'Brazil'), 'RU': ('🇷🇺', 'Russia'),
    'IT': ('🇮🇹', 'Italy'), 'ES': ('🇪🇸', 'Spain'), 'PL': ('🇵🇱', 'Poland'),
    'AT': ('🇦🇹', 'Austria'), 'BE': ('🇧🇪', 'Belgium'), 'IE': ('🇮🇪', 'Ireland'),
    'PT': ('🇵🇹', 'Portugal'), 'TR': ('🇹🇷', 'Turkey'), 'AE': ('🇦🇪', 'UAE'),
    'IL': ('🇮🇱', 'Israel'), 'RO': ('🇷🇴', 'Romania'), 'BG': ('🇧🇬', 'Bulgaria'),
    'CZ': ('🇨🇿', 'Czechia'), 'HU': ('🇭🇺', 'Hungary'), 'SK': ('🇸🇰', 'Slovakia'),
    'LT': ('🇱🇹', 'Lithuania'), 'LV': ('🇱🇻', 'Latvia'), 'EE': ('🇪🇪', 'Estonia'),
    'UA': ('🇺🇦', 'Ukraine'), 'MD': ('🇲🇩', 'Moldova'), 'RS': ('🇷🇸', 'Serbia'),
    'HR': ('🇭🇷', 'Croatia'), 'SI': ('🇸🇮', 'Slovenia'), 'GR': ('🇬🇷', 'Greece'),
    'CY': ('🇨🇾', 'Cyprus'), 'LU': ('🇱🇺', 'Luxembourg'), 'IS': ('🇮🇸', 'Iceland'),
    'KZ': ('🇰🇿', 'Kazakhstan'), 'VN': ('🇻🇳', 'Vietnam'), 'TH': ('🇹🇭', 'Thailand'),
    'MY': ('🇲🇾', 'Malaysia'), 'ID': ('🇮🇩', 'Indonesia'), 'PH': ('🇵🇭', 'Philippines'),
    'NZ': ('🇳🇿', 'New Zealand'), 'ZA': ('🇿🇦', 'South Africa'), 'EG': ('🇪🇬', 'Egypt'),
    'AR': ('🇦🇷', 'Argentina'), 'CL': ('🇨🇱', 'Chile'), 'CO': ('🇨🇴', 'Colombia'),
    'MX': ('🇲🇽', 'Mexico'), 'PE': ('🇵🇪', 'Peru'), 'UZ': ('🇺🇿', 'Uzbekistan'),
    'AZ': ('🇦🇿', 'Azerbaijan'), 'GE': ('🇬🇪', 'Georgia'), 'AM': ('🇦🇲', 'Armenia'),
    'BY': ('🇧🇾', 'Belarus'), 'KG': ('🇰🇬', 'Kyrgyzstan'), 'TJ': ('🇹🇯', 'Tajikistan'),
}

GARBAGE_WORDS = [
    'vk', 'the', 'cidr', 'proxy', 'vless', 'server', 'node',
    'free', 'vpn', 'config', 'list', 'white', 'mobile', 'rus',
    'tls', 'ws', 'grpc', 'reality', 'xtls', 'vision'
]


def load_geo_cache() -> Dict:
    if os.path.exists(GEO_CACHE_FILE):
        try:
            return json.load(open(GEO_CACHE_FILE, 'r', encoding='utf-8'))
        except:
            pass
    return {}


def save_geo_cache(cache: Dict):
    with open(GEO_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def get_ip(server: str) -> Optional[str]:
    try:
        ipaddress.ip_address(server)
        return server
    except ValueError:
        pass
    try:
        return socket.gethostbyname(server)
    except:
        pass
    try:
        info = socket.getaddrinfo(server, None, socket.AF_INET6)
        if info:
            return info[0][4][0]
    except:
        pass
    return None


def get_country_by_ip(ip: str) -> Optional[str]:
    cache = load_geo_cache()
    if ip in cache:
        return cache[ip]

    results = []

    def query(url, parser, timeout=3):
        try:
            r = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                code = parser(r)
                if code and len(code) == 2 and code.isalpha():
                    results.append(code.upper())
        except:
            pass

    query(f"http://ip-api.com/json/{ip}?fields=countryCode", lambda r: r.json().get('countryCode', ''))
    query(f"https://ipapi.co/{ip}/country/", lambda r: r.text.strip())
    query(f"https://ipwhois.app/json/{ip}", lambda r: r.json().get('country_code', ''))
    query(f"https://ifconfig.co/country?ip={ip}", lambda r: r.text.strip())
    query(f"https://ipinfo.io/{ip}/json", lambda r: r.json().get('country', ''))

    if not results:
        return None

    counter = Counter(results)
    code, count = counter.most_common(1)[0]

    cache[ip] = code
    save_geo_cache(cache)

    if len(results) >= 3 and count < len(results):
        logger.debug(f"  Geo conflict for {ip}: {results} → {code} ({count}/{len(results)})")

    return code


def clean_original_name(name: str) -> str:
    name = re.sub(r'[^\w\s\-.,]', ' ', name)
    name = re.sub(r'\[.*?\]', ' ', name)
    name = re.sub(r'\(.*?\)', ' ', name)
    name = re.sub(r'\*.*?\*', ' ', name)
    name_lower = name.lower()
    for word in GARBAGE_WORDS:
        name_lower = name_lower.replace(word, ' ')
    name = ' '.join(name_lower.split())
    name = name.title()
    return name.strip()


class VlessParser:
    @staticmethod
    def parse_uri(uri: str) -> Optional[Dict]:
        try:
            if not uri.startswith('vless://'):
                return None
            uri = uri[8:]
            if '#' in uri:
                uri_part, name = uri.split('#', 1)
                name = requests.utils.unquote(name.strip())
            else:
                uri_part, name = uri, ""
            if '?' in uri_part:
                base_part, params_str = uri_part.split('?', 1)
            else:
                base_part, params_str = uri_part, ''
            if '@' not in base_part:
                return None
            uuid_str, address_part = base_part.split('@', 1)
            port = 443
            if ':' in address_part:
                if address_part.count(':') > 1:
                    if ']:' in address_part:
                        address, port_str = address_part.rsplit(']:', 1)
                        address = address[1:]
                    else:
                        address, port_str = address_part, '443'
                else:
                    address, port_str = address_part.rsplit(':', 1)
                try:
                    port = int(port_str)
                except ValueError:
                    port = 443
            else:
                address = address_part
            params = {}
            if params_str:
                for param in params_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
            return {
                'uuid': uuid_str,
                'address': address,
                'port': port,
                'params': params,
                'original_name': name,
            }
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None

    @staticmethod
    def convert_to_flclash(data: Dict) -> Optional[Dict]:
        if not data:
            return None
        params = data.get('params', {})
        node = {
            'server': data['address'],
            'port': data['port'],
            'uuid': data['uuid'],
            'type': 'vless',
            'network': params.get('type', 'tcp'),
            'udp': True,
            'skip-cert-verify': True
        }
        security = params.get('security', '')
        if security == 'reality':
            node['tls'] = True
            node['reality-opts'] = {
                'public-key': params.get('pbk', ''),
                'short-id': params.get('sid', '')
            }
            if params.get('sni'):
                node['servername'] = params['sni']
            node['flow'] = params.get('flow', 'xtls-rprx-vision')
            node['client-fingerprint'] = params.get('fp', 'chrome')
        elif security == 'tls':
            node['tls'] = True
            node['servername'] = params.get('sni', data['address'])
            node['flow'] = params.get('flow', '')
            node['client-fingerprint'] = params.get('fp', 'chrome')
        net = node['network']
        if net == 'ws':
            node['ws-opts'] = {'path': params.get('path', '/'), 'headers': {}}
            if params.get('host'):
                node['ws-opts']['headers']['Host'] = params['host']
        elif net == 'grpc':
            node['grpc-opts'] = {'grpc-service-name': params.get('serviceName', '')}
        return node


def fetch_and_decode(url: str) -> List[str]:
    try:
        logger.info(f"📥 Downloading: {url}")
        r = requests.get(url, timeout=30, headers={'User-Agent': 'ClashX/1.0'})
        r.raise_for_status()
        content = r.text
        lines = []
        try:
            clean = content.strip()
            pad = 4 - len(clean) % 4 if len(clean) % 4 else 0
            clean += '=' * pad
            decoded = base64.b64decode(clean).decode('utf-8', errors='ignore')
            for line in decoded.split('\n'):
                if line.strip().startswith('vless://'):
                    lines.append(line.strip())
        except:
            for line in content.split('\n'):
                if line.strip().startswith('vless://'):
                    lines.append(line.strip())
        if not lines:
            found = re.findall(r'vless://[^\s]+', content)
            if found:
                lines.extend(found)
        logger.info(f"   Found {len(lines)} VLESS URIs")
        return lines
    except Exception as e:
        logger.error(f"   Download error: {e}")
        return []


def process_all_sources() -> List[Dict]:
    all_nodes = []
    parser = VlessParser()
    for url in SOURCES:
        uris = fetch_and_decode(url)
        for uri in uris:
            data = parser.parse_uri(uri)
            if data:
                node = parser.convert_to_flclash(data)
                if node and all(k in node for k in ['server', 'port', 'uuid']):
                    node['original_name'] = data['original_name']
                    all_nodes.append(node)
    return all_nodes


def finalize_names(nodes: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for node in nodes:
        nid = f"{node['server']}:{node['port']}:{node['uuid']}"
        if nid not in seen:
            seen.add(nid)
            unique.append(node)

    logger.info(f"Resolving GEO for {len(unique)} servers...")

    for i, node in enumerate(unique):
        if (i + 1) % 20 == 0:
            logger.info(f"  Progress: {i+1}/{len(unique)}")

        ip = get_ip(node['server'])
        country_code = get_country_by_ip(ip) if ip else None

        if country_code and country_code in COUNTRY_DATA:
            flag, country_name = COUNTRY_DATA[country_code]
            orig_clean = clean_original_name(node['original_name'])
            if orig_clean and orig_clean.lower() != country_name.lower():
                base_name = f"{flag} {country_name} - {orig_clean}"
            else:
                base_name = f"{flag} {country_name}"
        else:
            base_name = clean_original_name(node['original_name'])
            if not base_name:
                base_name = node['server']
        node['base_name'] = base_name

    name_counts = {}
    for node in unique:
        base = node['base_name']
        if base in name_counts:
            name_counts[base] += 1
            node['name'] = f"{base} #{name_counts[base]}"
        else:
            name_counts[base] = 1
            node['name'] = base

    dups = sum(1 for n in unique if '#' in n['name'])
    logger.info(f"Total: {len(unique)} | Numbered: {dups}")
    return unique


def update_history(nodes: List[Dict]):
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            history = json.load(open(HISTORY_FILE, 'r', encoding='utf-8'))
        except:
            pass
    now = datetime.now().isoformat()
    for node in nodes:
        h = hashlib.md5(f"{node['server']}:{node['port']}:{node['uuid']}".encode()).hexdigest()
        if h not in history:
            history[h] = {'first_seen': now, 'last_seen': now, 'name': node['name'], 'server': node['server'], 'port': node['port']}
        else:
            history[h]['last_seen'] = now
    json.dump(history, open(HISTORY_FILE, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


def generate_yaml(nodes: List[Dict]) -> str:
    if not nodes:
        return ""
    reality = [n for n in nodes if 'reality-opts' in n]
    tls = [n for n in nodes if n.get('tls') and 'reality-opts' not in n]

    y = f"""# FLClashX Subscription
# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Servers: {len(nodes)} (Reality: {len(reality)}, TLS: {len(tls)})

mixed-port: 7890
port: 7890
socks-port: 7891
allow-lan: true
mode: rule
log-level: info
ipv6: false
external-controller: 127.0.0.1:9090

dns:
  enable: true
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  default-nameserver:
    - 1.1.1.1
    - 8.8.8.8
  nameserver:
    - https://dns.cloudflare.com/dns-query

proxies:
"""
    for node in nodes:
        name = node['name'].replace('"', '\\"')
        y += f"  - name: \"{name}\"\n"
        y += f"    type: vless\n"
        y += f"    server: {node['server']}\n"
        y += f"    port: {node['port']}\n"
        y += f"    uuid: {node['uuid']}\n"
        y += f"    network: {node.get('network', 'tcp')}\n"
        y += f"    udp: true\n"
        y += f"    skip-cert-verify: true\n"
        if node.get('tls'):
            y += "    tls: true\n"
        if node.get('servername'):
            y += f"    servername: {node['servername']}\n"
        if node.get('flow'):
            y += f"    flow: {node['flow']}\n"
        if node.get('client-fingerprint'):
            y += f"    client-fingerprint: {node['client-fingerprint']}\n"
        if 'reality-opts' in node:
            r = node['reality-opts']
            y += "    reality-opts:\n"
            y += f"      public-key: \"{r.get('public-key', '')}\"\n"
            y += f"      short-id: \"{r.get('short-id', '')}\"\n"
        if 'ws-opts' in node:
            w = node['ws-opts']
            y += "    ws-opts:\n"
            y += f"      path: \"{w.get('path', '/')}\"\n"
            if w.get('headers'):
                y += "      headers:\n"
                for k, v in w['headers'].items():
                    y += f"        {k}: \"{v}\"\n"
        if 'grpc-opts' in node:
            y += "    grpc-opts:\n"
            y += f"      grpc-service-name: \"{node['grpc-opts'].get('grpc-service-name', '')}\"\n"
        y += "\n"

    y += "proxy-groups:\n"
    y += "  - name: 🚀 Auto\n    type: url-test\n    proxies:\n"
    for n in nodes[:20]:
        y += f"      - \"{n['name']}\"\n"
    y += "    url: http://www.gstatic.com/generate_204\n    interval: 300\n\n"

    y += "  - name: 📡 All Servers\n    type: select\n    proxies:\n      - 🚀 Auto\n"
    for n in nodes:
        y += f"      - \"{n['name']}\"\n"
    y += "\n"

    if reality:
        y += "  - name: 🔒 Reality\n    type: select\n    proxies:\n      - 🚀 Auto\n"
        for n in reality:
            y += f"      - \"{n['name']}\"\n"
        y += "\n"
    if tls:
        y += "  - name: 🔐 TLS\n    type: select\n    proxies:\n      - 🚀 Auto\n"
        for n in tls:
            y += f"      - \"{n['name']}\"\n"
        y += "\n"

    y += """rules:
  - DOMAIN-SUFFIX,local,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT
  - IP-CIDR,10.0.0.0/8,DIRECT
  - IP-CIDR,172.16.0.0/12,DIRECT
  - IP-CIDR,192.168.0.0/16,DIRECT
  - MATCH,🚀 Auto
"""
    return y


def main():
    logger.info("=" * 50)
    logger.info("FLClashX Subscription Merger")
    try:
        nodes = process_all_sources()
        if not nodes:
            logger.error("No servers found!")
            sys.exit(1)
        unique = finalize_names(nodes)
        update_history(unique)
        yaml = generate_yaml(unique)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(yaml)
        r = len([n for n in unique if 'reality-opts' in n])
        t = len([n for n in unique if n.get('tls') and 'reality-opts' not in n])
        logger.info(f"✅ Done! Total: {len(unique)} (Reality: {r}, TLS: {t})")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

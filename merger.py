#!/usr/bin/env python3
"""
VLESS Subscription Merger for FLClashX
Clean names with country flags, no duplicates
"""

import requests
import base64
import json
import hashlib
from datetime import datetime
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
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt"
]

OUTPUT_FILE = "merged_flclash.yaml"
HISTORY_FILE = "servers_history.json"

# Карта флагов стран
FLAGS = {
    'united kingdom': '🇬🇧', 'uk': '🇬🇧', 'england': '🇬🇧',
    'united states': '🇺🇸', 'usa': '🇺🇸', 'america': '🇺🇸',
    'germany': '🇩🇪', 'deutschland': '🇩🇪',
    'france': '🇫🇷',
    'netherlands': '🇳🇱', 'holland': '🇳🇱',
    'switzerland': '🇨🇭',
    'sweden': '🇸🇪',
    'norway': '🇳🇴',
    'finland': '🇫🇮',
    'denmark': '🇩🇰',
    'canada': '🇨🇦',
    'australia': '🇦🇺',
    'japan': '🇯🇵',
    'south korea': '🇰🇷', 'korea': '🇰🇷',
    'singapore': '🇸🇬',
    'hong kong': '🇭🇰',
    'taiwan': '🇹🇼',
    'china': '🇨🇳',
    'india': '🇮🇳',
    'brazil': '🇧🇷',
    'russia': '🇷🇺',
    'italy': '🇮🇹',
    'spain': '🇪🇸',
    'poland': '🇵🇱',
    'austria': '🇦🇹',
    'belgium': '🇧🇪',
    'ireland': '🇮🇪',
    'portugal': '🇵🇹',
    'turkey': '🇹🇷',
    'uae': '🇦🇪', 'dubai': '🇦🇪',
    'israel': '🇮🇱',
    'romania': '🇷🇴',
    'bulgaria': '🇧🇬',
    'czech': '🇨🇿', 'czechia': '🇨🇿',
    'hungary': '🇭🇺',
    'slovakia': '🇸🇰',
    'lithuania': '🇱🇹',
    'latvia': '🇱🇻',
    'estonia': '🇪🇪',
    'ukraine': '🇺🇦',
    'moldova': '🇲🇩',
    'serbia': '🇷🇸',
    'croatia': '🇭🇷',
    'slovenia': '🇸🇮',
    'greece': '🇬🇷',
    'cyprus': '🇨🇾',
    'luxembourg': '🇱🇺',
    'iceland': '🇮🇸',
}


def get_flag(name: str) -> str:
    """Определяет флаг по имени сервера"""
    name_lower = name.lower()
    for country, flag in FLAGS.items():
        if country in name_lower:
            return flag
    return ''


def clean_name(name: str) -> str:
    """Очищает имя от мусора, оставляя флаг и страну"""
    # Убираем emoji флаги (оставим свои)
    name = re.sub(r'[^\w\s\-.*#()\[\]@]', '', name)
    # Убираем лишние пробелы
    name = ' '.join(name.split())
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
                uri_part = uri
                name = ""

            if '?' in uri_part:
                base_part, params_str = uri_part.split('?', 1)
            else:
                base_part = uri_part
                params_str = ''

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
                        address = address_part
                        port_str = '443'
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
                'name': name if name else f"{address}:{port}",
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
            'name': data['name'],
            'type': 'vless',
            'server': data['address'],
            'port': data['port'],
            'uuid': data['uuid'],
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
            sni = params.get('sni', '')
            if sni:
                node['servername'] = sni
            flow = params.get('flow', 'xtls-rprx-vision')
            if flow:
                node['flow'] = flow
            node['client-fingerprint'] = params.get('fp', 'chrome')

        elif security == 'tls':
            node['tls'] = True
            node['servername'] = params.get('sni', data['address'])
            flow = params.get('flow', '')
            if flow:
                node['flow'] = flow
            node['client-fingerprint'] = params.get('fp', 'chrome')

        net = node['network']

        if net == 'ws':
            node['ws-opts'] = {
                'path': params.get('path', '/'),
                'headers': {}
            }
            host = params.get('host', '')
            if host:
                node['ws-opts']['headers']['Host'] = host

        elif net == 'grpc':
            node['grpc-opts'] = {
                'grpc-service-name': params.get('serviceName', '')
            }

        return node


def fetch_and_decode(url: str) -> List[str]:
    try:
        logger.info(f"Download: {url}")
        r = requests.get(url, timeout=30, headers={'User-Agent': 'ClashX/1.0'})
        r.raise_for_status()
        content = r.text
        logger.info(f"  Size: {len(content)} bytes")

        lines = []

        try:
            clean = content.strip()
            pad = 4 - len(clean) % 4 if len(clean) % 4 else 0
            clean += '=' * pad
            decoded = base64.b64decode(clean).decode('utf-8', errors='ignore')
            logger.info(f"  Base64 decoded: {len(decoded)} bytes")
            for line in decoded.split('\n'):
                line = line.strip()
                if line.startswith('vless://'):
                    lines.append(line)
        except:
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('vless://'):
                    lines.append(line)

        if not lines:
            found = re.findall(r'vless://[^\s]+', content)
            if found:
                lines.extend(found)

        logger.info(f"  VLESS found: {len(lines)}")
        return lines

    except Exception as e:
        logger.error(f"  Error: {e}")
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
                    all_nodes.append(node)

    return all_nodes


def make_beautiful_names(nodes: List[Dict]) -> List[Dict]:
    """
    Создает красивые уникальные имена с флагами.
    Формат: Флаг Страна (Server) или Флаг Страна - Город
    """
    # Сначала удаляем дубликаты по server:port:uuid
    seen = set()
    unique = []
    for node in nodes:
        nid = f"{node['server']}:{node['port']}:{node['uuid']}"
        if nid not in seen:
            seen.add(nid)
            unique.append(node)

    # Создаем красивые имена
    name_pool = {}
    for node in unique:
        original = clean_name(node['name'])
        flag = get_flag(original)
        
        # Если флаг уже есть в имени - оставляем как есть
        if flag and flag not in original:
            # Создаем имя с флагом
            # Убираем мусорные теги
            clean = re.sub(r'\[.*?\]', '', original).strip()
            clean = re.sub(r'\(.*?\)', '', clean).strip()
            clean = re.sub(r'\*.*?\*', '', clean).strip()
            clean = ' '.join(clean.split())
            
            if not clean:
                clean = node['server']
            
            # Базовая часть: флаг + название
            base = f"{flag} {clean}"
        else:
            base = original if original else node['server']
        
        # Если есть дубликат имени - добавляем адрес
        if base in name_pool:
            name_pool[base] += 1
            final_name = f"{base} ({node['server']})"
        else:
            name_pool[base] = 1
            final_name = base
        
        node['name'] = final_name

    logger.info(f"Unique servers: {len(unique)} (duplicates removed: {len(nodes) - len(unique)})")
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
            history[h] = {
                'first_seen': now,
                'last_seen': now,
                'name': node['name'],
                'server': node['server'],
                'port': node['port']
            }
        else:
            history[h]['last_seen'] = now

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


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
    - https://dns.google/dns-query

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
    y += "  - name: 🚀 Auto\n"
    y += "    type: url-test\n"
    y += "    proxies:\n"
    for n in nodes[:20]:
        y += f"      - \"{n['name']}\"\n"
    y += "    url: http://www.gstatic.com/generate_204\n"
    y += "    interval: 300\n\n"

    y += "  - name: 📡 All Servers\n"
    y += "    type: select\n"
    y += "    proxies:\n"
    y += "      - 🚀 Auto\n"
    for n in nodes:
        y += f"      - \"{n['name']}\"\n"
    y += "\n"

    if reality:
        y += "  - name: 🔒 Reality\n"
        y += "    type: select\n"
        y += "    proxies:\n"
        y += "      - 🚀 Auto\n"
        for n in reality:
            y += f"      - \"{n['name']}\"\n"
        y += "\n"

    if tls:
        y += "  - name: 🔐 TLS\n"
        y += "    type: select\n"
        y += "    proxies:\n"
        y += "      - 🚀 Auto\n"
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
    logger.info("=" * 50)

    try:
        nodes = process_all_sources()
        if not nodes:
            logger.error("No servers found!")
            sys.exit(1)

        unique = make_beautiful_names(nodes)
        update_history(unique)

        yaml = generate_yaml(unique)
        if not yaml:
            logger.error("Failed to generate config!")
            sys.exit(1)

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(yaml)

        r = len([n for n in unique if 'reality-opts' in n])
        t = len([n for n in unique if n.get('tls') and 'reality-opts' not in n])

        logger.info(f"Done! Servers: {len(unique)} (Reality: {r}, TLS: {t})")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

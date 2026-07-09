#!/usr/bin/env python3
"""
Объединение VLESS подписок в формат FLClashX
Оптимизировано для iOS/macOS
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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# URL исходных подписок
SOURCES = [
    "https://raw.githubusercontent.com/GoldCaviar/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt"
]

OUTPUT_FILE = "merged_flclash.yaml"
HISTORY_FILE = "servers_history.json"

class VlessParser:
    """Парсер VLESS URI для FLClashX"""
    
    # Счетчик для уникальных имен
    name_counter = {}
    
    @staticmethod
    def sanitize_name(name: str, server: str = "", port: int = 0) -> str:
        """Очистка и создание уникального имени сервера"""
        # Удаляем проблемные символы
        name = re.sub(r'[^\w\s\-_@#.]', '', name)
        
        # Если имя пустое или слишком короткое
        if not name or len(name.strip()) < 3:
            name = f"VLESS-{server}-{port}"
        
        # Ограничиваем длину
        if len(name) > 45:
            name = name[:42] + "..."
        
        # Делаем имя уникальным
        base_name = name.strip()
        if base_name in VlessParser.name_counter:
            VlessParser.name_counter[base_name] += 1
            name = f"{base_name} #{VlessParser.name_counter[base_name]}"
        else:
            VlessParser.name_counter[base_name] = 0
            name = base_name
        
        return name
    
    @staticmethod
    def parse_uri(uri: str) -> Optional[Dict]:
        """Парсит VLESS URI с полной поддержкой всех параметров"""
        try:
            if not uri.startswith('vless://'):
                return None
            
            uri_original = uri
            uri = uri[8:]
            
            # Извлекаем имя из фрагмента
            if '#' in uri:
                uri_part, name = uri.split('#', 1)
                name = requests.utils.unquote(name.strip())
            else:
                uri_part = uri
                name = ""
            
            # Парсим основную часть
            if '?' in uri_part:
                base_part, params_str = uri_part.split('?', 1)
            else:
                base_part = uri_part
                params_str = ''
            
            if '@' not in base_part:
                return None
            
            uuid_str, address_part = base_part.split('@', 1)
            
            # Парсим адрес и порт
            port = 443
            if ':' in address_part:
                if address_part.count(':') > 1:
                    # IPv6
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
            
            # Парсим параметры
            params = {}
            if params_str:
                for param in params_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
            
            # Если имя не задано, создаем из параметров
            if not name:
                country = params.get('country', '')
                city = params.get('city', '')
                if country:
                    name = country
                    if city:
                        name += f" - {city}"
                else:
                    name = f"{address}:{port}"
            
            # Создаем уникальное имя
            name = VlessParser.sanitize_name(name, address, port)
            
            # Добавляем префикс типа безопасности
            security = params.get('security', '')
            if security == 'reality':
                if not name.startswith('[R]'):
                    name = f"[R] {name}"
            elif security == 'tls':
                if not name.startswith('[T]'):
                    name = f"[T] {name}"
            
            # Добавляем тип транспорта
            network = params.get('type', 'tcp')
            if network == 'ws':
                if '[WS]' not in name:
                    name = f"{name} [WS]"
            elif network == 'grpc':
                if '[gRPC]' not in name:
                    name = f"{name} [gRPC]"
            
            return {
                'uuid': uuid_str,
                'address': address,
                'port': port,
                'params': params,
                'name': name,
                'original_uri': f"vless://{uri}"
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга URI: {e}")
            return None
    
    @staticmethod
    def convert_to_flclash(data: Dict) -> Optional[Dict]:
        """Конвертирует в формат FLClashX"""
        if not data:
            return None
        
        params = data.get('params', {})
        
        flclash_node = {
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
            flclash_node['tls'] = True
            flclash_node['reality-opts'] = {
                'public-key': params.get('pbk', ''),
                'short-id': params.get('sid', '')
            }
            
            sni = params.get('sni', '')
            if sni:
                flclash_node['servername'] = sni
            
            flow = params.get('flow', 'xtls-rprx-vision')
            if flow:
                flclash_node['flow'] = flow
            
            fp = params.get('fp', 'chrome')
            flclash_node['client-fingerprint'] = fp
        
        elif security == 'tls':
            flclash_node['tls'] = True
            sni = params.get('sni', data['address'])
            flclash_node['servername'] = sni
            
            flow = params.get('flow', '')
            if flow:
                flclash_node['flow'] = flow
            
            fp = params.get('fp', 'chrome')
            flclash_node['client-fingerprint'] = fp
            
            alpn = params.get('alpn', '')
            if alpn:
                flclash_node['alpn'] = [alpn]
        
        network_type = flclash_node['network']
        
        if network_type == 'ws':
            ws_opts = {
                'path': params.get('path', '/'),
                'headers': {}
            }
            
            host = params.get('host', '')
            if host:
                ws_opts['headers']['Host'] = host
            
            flclash_node['ws-opts'] = ws_opts
        
        elif network_type == 'grpc':
            service_name = params.get('serviceName', '')
            flclash_node['grpc-opts'] = {
                'grpc-service-name': service_name if service_name else ''
            }
        
        elif network_type in ['h2', 'http']:
            flclash_node['network'] = 'h2'
            h2_opts = {
                'path': params.get('path', '/')
            }
            
            host = params.get('host', '')
            if host:
                h2_opts['host'] = [host]
            
            flclash_node['h2-opts'] = h2_opts
        
        elif network_type == 'xhttp':
            flclash_node['xhttp-opts'] = {
                'path': params.get('path', '/'),
                'mode': params.get('mode', 'packet-up')
            }
            
            host = params.get('host', '')
            if host:
                flclash_node['xhttp-opts']['host'] = host
        
        return flclash_node

def fetch_and_decode(url: str) -> List[str]:
    """Загружает подписку и извлекает VLESS URI"""
    try:
        logger.info(f"📥 Загрузка: {url}")
        
        headers = {
            'User-Agent': 'ClashX/1.0 (iOS)',
            'Accept': 'text/plain, application/octet-stream'
        }
        
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        content = response.text
        logger.info(f"Получено {len(content)} байт")
        
        vless_lines = []
        
        # Способ 1: Декодируем base64 с правильным padding
        try:
            content_clean = content.strip()
            missing_padding = len(content_clean) % 4
            if missing_padding:
                content_clean += '=' * (4 - missing_padding)
            
            decoded_bytes = base64.b64decode(content_clean)
            decoded = decoded_bytes.decode('utf-8', errors='ignore')
            logger.info(f"✅ Base64 декодирован, размер: {len(decoded)} байт")
            
            for line in decoded.split('\n'):
                line = line.strip()
                if line.startswith('vless://'):
                    vless_lines.append(line)
                    
        except Exception as e:
            logger.debug(f"Способ 1 не сработал: {e}")
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('vless://'):
                    vless_lines.append(line)
        
        # Способ 2: Поиск через regex
        if not vless_lines and len(content) > 100:
            logger.info("🔍 Поиск через регулярное выражение...")
            pattern = r'vless://[a-zA-Z0-9\-_]+@[^:\s]+:\d+\?[^\s]+'
            matches = re.findall(pattern, content)
            if matches:
                vless_lines.extend(matches)
                logger.info(f"Найдено через regex: {len(matches)} URI")
        
        # Способ 3: Пробуем latin-1 декодирование
        if not vless_lines and len(content) > 100:
            try:
                content_clean = content.strip()
                missing_padding = len(content_clean) % 4
                if missing_padding:
                    content_clean += '=' * (4 - missing_padding)
                decoded_latin = base64.b64decode(content_clean).decode('latin-1')
                pattern = r'vless://[a-zA-Z0-9\-_]+@[^:\s]+:\d+\?[^\s]+'
                matches = re.findall(pattern, decoded_latin)
                if matches:
                    vless_lines.extend(matches)
                    logger.info(f"Найдено в latin-1: {len(matches)} URI")
            except:
                pass
        
        logger.info(f"✅ Всего найдено {len(vless_lines)} VLESS URI")
        
        if not vless_lines:
            logger.warning(f"⚠️ VLESS не найдены! Первые 200 символов: {content[:200]}")
        
        return vless_lines
        
    except requests.RequestException as e:
        logger.error(f"❌ Ошибка загрузки {url}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка обработки {url}: {e}")
        return []

def process_all_sources() -> List[Dict]:
    """Обрабатывает все источники"""
    # Сбрасываем счетчик имен перед обработкой
    VlessParser.name_counter = {}
    
    all_nodes = []
    parser = VlessParser()
    
    for url in SOURCES:
        vless_uris = fetch_and_decode(url)
        
        for uri in vless_uris:
            try:
                vless_data = parser.parse_uri(uri)
                
                if vless_data:
                    flclash_node = parser.convert_to_flclash(vless_data)
                    
                    if flclash_node:
                        if all(k in flclash_node for k in ['server', 'port', 'uuid']):
                            all_nodes.append(flclash_node)
                        else:
                            logger.warning(f"⚠️ Нет обязательных полей: {flclash_node.get('name', 'Unknown')}")
                    else:
                        logger.warning(f"⚠️ Не удалось конвертировать: {vless_data.get('name', 'Unknown')}")
                else:
                    logger.warning(f"⚠️ Не удалось распарсить URI")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка обработки URI: {e}")
                continue
    
    return all_nodes

def remove_duplicates(nodes: List[Dict]) -> List[Dict]:
    """Удаляет дубликаты узлов"""
    seen = set()
    unique = []
    
    for node in nodes:
        node_id = f"{node.get('server', '')}:{node.get('port', 0)}:{node.get('uuid', '')}"
        
        if node_id not in seen:
            seen.add(node_id)
            unique.append(node)
    
    logger.info(f"🗑️ Удалено дубликатов: {len(nodes) - len(unique)}")
    return unique

def update_history(nodes: List[Dict]):
    """Обновляет историю серверов"""
    history = {}
    
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            history = {}
    
    current_time = datetime.now().isoformat()
    
    for node in nodes:
        node_hash = hashlib.md5(
            f"{node['server']}:{node['port']}:{node['uuid']}".encode()
        ).hexdigest()
        
        if node_hash not in history:
            history[node_hash] = {
                'first_seen': current_time,
                'last_seen': current_time,
                'name': node['name'],
                'server': node['server'],
                'port': node['port'],
                'type': node.get('type', 'vless'),
                'reality': 'reality-opts' in node
            }
        else:
            history[node_hash]['last_seen'] = current_time
            history[node_hash]['name'] = node['name']
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def generate_flclash_yaml(nodes: List[Dict]) -> str:
    """Генерирует YAML конфигурацию для FLClashX"""
    if not nodes:
        logger.error("❌ Нет узлов для генерации!")
        return ""
    
    reality_nodes = [n for n in nodes if 'reality-opts' in n]
    tls_nodes = [n for n in nodes if n.get('tls') and 'reality-opts' not in n]
    other_nodes = [n for n in nodes if not n.get('tls')]
    
    yaml = f"""# ===========================================
# FLClashX Subscription
# ===========================================
# Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Серверов: {len(nodes)}
# Reality: {len(reality_nodes)} | TLS: {len(tls_nodes)} | Другие: {len(other_nodes)}
# ===========================================

mixed-port: 7890
port: 7890
socks-port: 7891
allow-lan: true
mode: rule
log-level: info
ipv6: false
external-controller: 127.0.0.1:9090
secret: ''

dns:
  enable: true
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  listen: 0.0.0.0:53
  default-nameserver:
    - 1.1.1.1
    - 8.8.8.8
  nameserver:
    - https://dns.cloudflare.com/dns-query
    - https://dns.google/dns-query
    - 1.1.1.1
    - 8.8.8.8
  fallback:
    - https://dns.quad9.net/dns-query
    - tls://8.8.8.8:853
  fallback-filter:
    geoip: true
    ipcidr:
      - 240.0.0.0/4
      - 0.0.0.0/32

proxies:
"""
    
    for idx, node in enumerate(nodes, 1):
        try:
            name = node.get('name', f'Server-{idx}')
            name_escaped = name.replace('"', '\\"').replace("'", "\\'")
            
            yaml += f"  - name: \"{name_escaped}\"\n"
            yaml += f"    type: vless\n"
            yaml += f"    server: {node['server']}\n"
            yaml += f"    port: {node['port']}\n"
            yaml += f"    uuid: {node['uuid']}\n"
            yaml += f"    network: {node.get('network', 'tcp')}\n"
            yaml += f"    udp: true\n"
            yaml += f"    skip-cert-verify: true\n"
            
            if node.get('tls'):
                yaml += "    tls: true\n"
            
            if node.get('servername'):
                yaml += f"    servername: {node['servername']}\n"
            
            if node.get('flow'):
                yaml += f"    flow: {node['flow']}\n"
            
            if node.get('client-fingerprint'):
                yaml += f"    client-fingerprint: {node['client-fingerprint']}\n"
            
            if 'reality-opts' in node:
                reality = node['reality-opts']
                yaml += "    reality-opts:\n"
                yaml += f"      public-key: \"{reality.get('public-key', '')}\"\n"
                yaml += f"      short-id: \"{reality.get('short-id', '')}\"\n"
            
            if 'ws-opts' in node:
                ws = node['ws-opts']
                yaml += "    ws-opts:\n"
                if 'path' in ws:
                    yaml += f"      path: \"{ws['path']}\"\n"
                if 'headers' in ws:
                    yaml += "      headers:\n"
                    for k, v in ws['headers'].items():
                        yaml += f"        {k}: \"{v}\"\n"
            
            if 'grpc-opts' in node:
                grpc = node['grpc-opts']
                yaml += "    grpc-opts:\n"
                if 'grpc-service-name' in grpc:
                    yaml += f"      grpc-service-name: \"{grpc['grpc-service-name']}\"\n"
            
            if 'h2-opts' in node:
                h2 = node['h2-opts']
                yaml += "    h2-opts:\n"
                if 'path' in h2:
                    yaml += f"      path: \"{h2['path']}\"\n"
                if 'host' in h2:
                    yaml += "      host:\n"
                    for host in h2['host']:
                        yaml += f"        - {host}\n"
            
            if 'xhttp-opts' in node:
                xhttp = node['xhttp-opts']
                yaml += "    xhttp-opts:\n"
                if 'path' in xhttp:
                    yaml += f"      path: \"{xhttp['path']}\"\n"
                if 'mode' in xhttp:
                    yaml += f"      mode: \"{xhttp['mode']}\"\n"
                if 'host' in xhttp:
                    yaml += f"      host: \"{xhttp['host']}\"\n"
            
            if 'alpn' in node:
                yaml += "    alpn:\n"
                for a in node['alpn']:
                    yaml += f"      - {a}\n"
            
            yaml += "\n"
            
        except Exception as e:
            logger.error(f"❌ Ошибка при записи узла {name}: {e}")
            continue
    
    yaml += "proxy-groups:\n"
    
    yaml += "  - name: 🚀 Auto\n"
    yaml += "    type: url-test\n"
    yaml += "    proxies:\n"
    for node in nodes[:20]:
        name_escaped = node['name'].replace('"', '\\"')
        yaml += f"      - \"{name_escaped}\"\n"
    yaml += "    url: http://www.gstatic.com/generate_204\n"
    yaml += "    interval: 300\n"
    yaml += "    tolerance: 100\n\n"
    
    yaml += "  - name: 📡 All Servers\n"
    yaml += "    type: select\n"
    yaml += "    proxies:\n"
    yaml += "      - 🚀 Auto\n"
    yaml += "      - DIRECT\n"
    yaml += "      - REJECT\n"
    for node in nodes:
        name_escaped = node['name'].replace('"', '\\"')
        yaml += f"      - \"{name_escaped}\"\n"
    yaml += "\n"
    
    if reality_nodes:
        yaml += "  - name: 🔒 Reality\n"
        yaml += "    type: select\n"
        yaml += "    proxies:\n"
        yaml += "      - 🚀 Auto\n"
        for node in reality_nodes:
            name_escaped = node['name'].replace('"', '\\"')
            yaml += f"      - \"{name_escaped}\"\n"
        yaml += "\n"
    
    if tls_nodes:
        yaml += "  - name: 🔐 TLS\n"
        yaml += "    type: select\n"
        yaml += "    proxies:\n"
        yaml += "      - 🚀 Auto\n"
        for node in tls_nodes:
            name_escaped = node['name'].replace('"', '\\"')
            yaml += f"      - \"{name_escaped}\"\n"
        yaml += "\n"
    
    yaml += """rule-providers:
  reject:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt"
    path: ./ruleset/reject.yaml
    interval: 86400

rules:
  - DOMAIN-SUFFIX,local,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT
  - IP-CIDR,10.0.0.0/8,DIRECT
  - IP-CIDR,172.16.0.0/12,DIRECT
  - IP-CIDR,192.168.0.0/16,DIRECT
  - RULE-SET,reject,REJECT
  - MATCH,🚀 Auto
"""
    
    return yaml

def main():
    """Основная функция"""
    logger.info("="*60)
    logger.info("🚀 FLClashX Subscription Merger")
    logger.info("="*60)
    
    try:
        logger.info("📥 Загрузка подписок...")
        all_nodes = process_all_sources()
        
        if not all_nodes:
            logger.error("❌ Не удалось получить серверы!")
            sys.exit(1)
        
        logger.info(f"✅ Загружено: {len(all_nodes)} серверов")
        
        logger.info("🔍 Удаление дубликатов...")
        unique_nodes = remove_duplicates(all_nodes)
        
        logger.info("📝 Обновление истории...")
        update_history(unique_nodes)
        
        logger.info("⚙️ Генерация FLClashX конфигурации...")
        yaml_config = generate_flclash_yaml(unique_nodes)
        
        if not yaml_config:
            logger.error("❌ Не удалось сгенерировать конфиг!")
            sys.exit(1)
        
        logger.info(f"💾 Сохранение в {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(yaml_config)
        
        reality_count = len([n for n in unique_nodes if 'reality-opts' in n])
        tls_count = len([n for n in unique_nodes if n.get('tls') and 'reality-opts' not in n])
        
        logger.info("="*60)
        logger.info("✅ ГОТОВО!")
        logger.info(f"📊 Серверов: {len(unique_nodes)}")
        logger.info(f"   🔒 Reality: {reality_count}")
        logger.info(f"   🔐 TLS: {tls_count}")
        logger.info(f"📱 Файл: {OUTPUT_FILE}")
        logger.info("="*60)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

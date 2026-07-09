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
        
        # Способ 1: Пробуем декодировать как base64 с правильным padding
        try:
            # Добавляем правильный padding
            content_clean = content.strip()
            missing_padding = len(content_clean) % 4
            if missing_padding:
                content_clean += '=' * (4 - missing_padding)
            
            decoded_bytes = base64.b64decode(content_clean)
            decoded = decoded_bytes.decode('utf-8', errors='ignore')
            logger.info(f"✅ Base64 декодирован успешно, размер: {len(decoded)} байт")
            
            # Ищем все vless:// URI
            for line in decoded.split('\n'):
                line = line.strip()
                if line.startswith('vless://'):
                    vless_lines.append(line)
                    logger.debug(f"Найден VLESS: {line[:50]}...")
                    
        except Exception as e:
            logger.debug(f"Способ 1 не сработал: {e}")
            
            # Способ 2: Ищем vless:// напрямую в тексте
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('vless://'):
                    vless_lines.append(line)
        
        # Способ 3: Поиск через регулярное выражение (если ничего не нашли)
        if not vless_lines and len(content) > 100:
            logger.info("🔍 Поиск через регулярное выражение...")
            import re
            # Ищем все vless:// URI в сыром тексте
            pattern = r'vless://[a-zA-Z0-9\-_]+@[^:\s]+:\d+\?[^\s]+'
            matches = re.findall(pattern, content)
            if matches:
                vless_lines.extend(matches)
                logger.info(f"Найдено через regex: {len(matches)} URI")
            
            # Если все еще нет - пробуем поискать в base64 декодированном тексте
            if not vless_lines:
                try:
                    decoded_search = base64.b64decode(content_clean).decode('latin-1')
                    vless_matches = re.findall(pattern, decoded_search)
                    if vless_matches:
                        vless_lines.extend(vless_matches)
                        logger.info(f"Найдено в latin-1 декодировании: {len(vless_matches)} URI")
                except:
                    pass
        
        logger.info(f"✅ Всего найдено {len(vless_lines)} VLESS URI")
        
        # Логируем примеры для отладки
        if vless_lines:
            logger.debug(f"Пример URI: {vless_lines[0][:100]}...")
        else:
            logger.warning(f"⚠️ Не найдено ни одного VLESS URI!")
            logger.debug(f"Первые 200 символов контента: {content[:200]}")
        
        return vless_lines
        
    except requests.RequestException as e:
        logger.error(f"❌ Ошибка загрузки {url}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка обработки {url}: {e}")
        return []

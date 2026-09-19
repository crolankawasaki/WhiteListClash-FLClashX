#!/usr/bin/env python3
"""
Кодирует YAML конфигурацию в base64 для FLClashX
"""

import base64
import sys
import os
from datetime import datetime

def encode_subscription():
    """Кодирует merged_flclash.yaml в base64"""
    try:
        # Проверяем существование файла
        if not os.path.exists('merged_flclash.yaml'):
            print("❌ Файл merged_flclash.yaml не найден!")
            print("💡 Сначала запустите merger.py")
            # Создаем пустые файлы чтобы git не падал
            with open('merged_flclash_base64.txt', 'w') as f:
                f.write('')
            with open('subscription_info.txt', 'w') as f:
                f.write('# No data yet')
            sys.exit(0)
        
        # Читаем YAML файл
        with open('merged_flclash.yaml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            print("❌ Файл merged_flclash.yaml пуст!")
            with open('merged_flclash_base64.txt', 'w') as f:
                f.write('')
            with open('subscription_info.txt', 'w') as f:
                f.write('# Empty subscription')
            sys.exit(0)
        
        # Кодируем в base64
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Сохраняем base64 версию
        with open('merged_flclash_base64.txt', 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        # Создаем информационный файл (обязательно создаем!)
        info = f"""# FLClashX Subscription Info
# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Format: Base64 encoded YAML
# Original file: merged_flclash.yaml
# Use this URL for direct import in FLClashX
"""
        with open('subscription_info.txt', 'w', encoding='utf-8') as f:
            f.write(info)
        
        print(f"✅ Base64 подписка сохранена")
        print(f"📏 Размер: {len(encoded)} символов")
        print(f"💾 Файлы созданы: merged_flclash_base64.txt, subscription_info.txt")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        # Создаем файлы чтобы workflow не падал
        with open('merged_flclash_base64.txt', 'w') as f:
            f.write('')
        with open('subscription_info.txt', 'w') as f:
            f.write('# Error occurred')
        sys.exit(0)  # Выходим без ошибки

if __name__ == "__main__":
    encode_subscription()

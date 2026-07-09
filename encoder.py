#!/usr/bin/env python3
"""Кодирует YAML в base64 для прямой подписки FLClashX"""

import base64
import sys

def encode_subscription():
    try:
        with open('merged_flclash.yaml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Кодируем в base64
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Сохраняем
        with open('merged_flclash_base64.txt', 'w') as f:
            f.write(encoded)
        
        print(f"✅ Base64 подписка сохранена в merged_flclash_base64.txt")
        print(f"📏 Размер: {len(encoded)} символов")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    encode_subscription()

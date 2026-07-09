# 🚀 FLClashX VLESS Subscription

[![Update Subscription](https://github.com/crolankawasaki/WhiteListClash-FLClashX/actions/workflows/update-subscription.yml/badge.svg)](https://github.com/crolankawasaki/WhiteListClash-FLClashX/actions/workflows/update-subscription.yml)
[![Servers](https://img.shields.io/badge/Updated-Every%20Hour-blue)](https://github.com/crolankawasaki/WhiteListClash-FLClashX)

> Автоматически обновляемая VLESS подписка для FLClashX (iOS/macOS)
> 
> Серверы собираются из проверенных источников каждый час

---

## 📥 Подписка
https://raw.githubusercontent.com/crolankawasaki/WhiteListClash-FLClashX/main/merged_flclash.yaml

---

## 📱 Как установить

### iOS (iPhone/iPad)

1. Откройте **FLClashX**
2. Перейдите в **Config** (внизу)
3. Нажмите **+** → **URL**
4. Вставьте ссылку: https://raw.githubusercontent.com/crolankawasaki/WhiteListClash-FLClashX/main/merged_flclash.yaml
5. Нажмите **Download**
6. Выберите скачанный конфиг (появится ✅)
7. Вернитесь на главный экран
8. Нажмите переключатель для запуска

### macOS

1. Откройте **FLClashX**
2. Иконка в строке меню → **Config** → **Remote Config** → **Add**
3. Вставьте ссылку
4. Включите автообновление (интервал 3600)

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 🔄 Автообновление | Каждый час через GitHub Actions |
| 🔒 Reality | Обход DPI и блокировок |
| 🔐 TLS | Стандартное шифрование |
| 🚀 Auto-выбор | Автоматически выбирает быстрейший сервер |
| 🗑️ Дедупликация | Удаляет повторяющиеся серверы |
| 📊 История | Отслеживает появление новых серверов |

---

## 📋 Группы серверов

| Группа | Тип | Описание |
|--------|-----|----------|
| 🚀 **Auto** | url-test | Авто-выбор быстрейшего (каждые 5 мин) |
| 📡 **All Servers** | select | Все доступные серверы |
| 🔒 **Reality** | select | Только Reality протокол |
| 🔐 **TLS** | select | Только TLS шифрование |

---

## 🔄 Как работает обновление 
```

Каждый час:
📥 Скачиваются свежие списки серверов
🔄 Объединяются в один файл
🗑️ Удаляются дубликаты
💾 Сохраняется новая подписка
📱 FLClashX автоматически подхватывает


---

## 📁 Файлы в репозитории

| Файл | Назначение |
|------|------------|
| `merged_flclash.yaml` | Готовая подписка для FLClashX |
| `merged_flclash_base64.txt` | Base64 версия подписки |
| `servers_history.json` | История серверов |
| `merger.py` | Скрипт объединения |
| `encoder.py` | Кодирование в base64 |

---

## 🛠 Источники серверов

1. **GoldCaviar** — VLESS Reality White List (Russia Mobile)
2. **zieng2** — VLESS Universal

---

## ⚠️ Важно

- Все серверы предоставляются бесплатно
- Скорость зависит от загрузки серверов
- Используйте **🚀 Auto** для автоматического выбора
- Если не работает — попробуйте группу **🔒 Reality**

---

## 💡 Советы

**Если медленно:**
- Подождите 5 минут, Auto сам найдет быстрый сервер
- Попробуйте вручную выбрать сервер из списка

**Если не подключается:**
- Проверьте группу 🔒 Reality
- Обновите подписку (потяните вниз в Config)
- Перезапустите FLClashX

**Если закончился трафик:**
- Серверы обновляются каждый час
- Новые серверы появляются автоматически

---

## 📊 Статус

- ✅ Автообновление: работает
- ✅ Серверы: обновляются каждый час
- ✅ FLClashX: полностью совместимо

---

## 📝 Лицензия

MIT — используйте свободно

---

⭐ **Поставьте звезду**, если подписка оказалась полезной!

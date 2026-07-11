# --- Geo Utilities (полная замена) ---
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
    """
    Разрешает домен в IP.
    Пробует IPv4, если не получается — IPv6.
    """
    # Уже IP
    try:
        ipaddress.ip_address(server)
        return server
    except ValueError:
        pass
    
    # Пробуем IPv4
    try:
        return socket.gethostbyname(server)
    except:
        pass
    
    # Пробуем IPv6
    try:
        info = socket.getaddrinfo(server, None, socket.AF_INET6)
        if info:
            return info[0][4][0]
    except:
        pass
    
    return None

def get_country_by_ip(ip: str) -> Optional[str]:
    """
    Опрашивает НЕСКОЛЬКО сервисов геолокации.
    Возвращает страну, которую вернуло БОЛЬШИНСТВО.
    """
    cache = load_geo_cache()
    if ip in cache:
        return cache[ip]
    
    results = []
    
    # Сервис 1: ip-api.com
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=5)
        if r.status_code == 200:
            code = r.json().get('countryCode', '')
            if len(code) == 2:
                results.append(code)
    except:
        pass
    
    # Сервис 2: ipapi.co
    try:
        r = requests.get(f"https://ipapi.co/{ip}/country/", timeout=5, 
                        headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            code = r.text.strip()
            if len(code) == 2:
                results.append(code)
    except:
        pass
    
    # Сервис 3: ipwhois.app
    try:
        r = requests.get(f"https://ipwhois.app/json/{ip}", timeout=5)
        if r.status_code == 200:
            code = r.json().get('country_code', '')
            if len(code) == 2:
                results.append(code)
    except:
        pass
    
    # Сервис 4: ifconfig.co
    try:
        r = requests.get(f"https://ifconfig.co/country?ip={ip}", timeout=5)
        if r.status_code == 200:
            code = r.text.strip()
            if len(code) == 2:
                results.append(code)
    except:
        pass
    
    # Сервис 5: ipinfo.io
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        if r.status_code == 200:
            code = r.json().get('country', '')
            if len(code) == 2:
                results.append(code)
    except:
        pass
    
    if not results:
        return None
    
    # Выбираем самый частый ответ (большинство)
    from collections import Counter
    counter = Counter(results)
    most_common = counter.most_common(1)[0]
    code = most_common[0]
    
    # Сохраняем в кэш только если хотя бы 2 сервиса согласны
    # или если ответил только 1 сервис
    if most_common[1] >= 2 or len(results) == 1:
        cache[ip] = code
        save_geo_cache(cache)
        return code
    
    # Если сервисы разошлись во мнениях — берём первый ответ
    code = results[0]
    cache[ip] = code
    save_geo_cache(cache)
    return code

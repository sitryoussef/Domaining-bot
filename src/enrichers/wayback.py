import requests

def wayback_snapshot_score(domain: str, cap: int = 40, weight: float = 0.5) -> float:
    # Compte approximatif de snapshots pour scorer l'historique
    try:
        r = requests.get(
            "https://web.archive.org/cdx/search/cdx",
            params={"url": domain, "output": "json", "fl": "timestamp", "collapse": "timestamp:8"},
            timeout=10
        )
        if r.status_code != 200:
            return 0.0
        data = r.json()
        # 1ère ligne est l'entête
        count = max(len(data) - 1, 0)
        count = min(count, cap)  # caper
        return count * weight
    except:
        return 0.0

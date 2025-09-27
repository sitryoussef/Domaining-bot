import requests

def rdap_age_years(domain: str) -> int:
    # estimation via RDAP public (gratuit)
    try:
        tld = domain.split(".")[-1]
        url = f"https://rdap.org/domain/{domain}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return 0
        j = r.json()
        events = j.get("events", [])
        # chercher "registration" ou "created"
        for ev in events:
            if ev.get("eventAction") in ("registration", "create", "created"):
                date = ev.get("eventDate", "")
                year = int(date[:4]) if len(date) >= 4 else 0
                if year:
                    from datetime import datetime
                    return max(0, datetime.utcnow().year - year)
        return 0
    except:
        return 0

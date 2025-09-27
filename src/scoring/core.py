import yaml, re
from . import __init__  # noop just to allow package style if needed

def load_rules(path): 
    with open(path, "r", encoding="utf-8") as f: 
        return yaml.safe_load(f)

def load_niches(path): 
    with open(path, "r", encoding="utf-8") as f: 
        return yaml.safe_load(f)

def base_features(domain: str):
    name, _, tld = domain.lower().partition(".")
    length = len(name)
    hyphens = name.count("-")
    digits = sum(ch.isdigit() for ch in name)
    return name, tld, length, hyphens, digits

def brandable(name: str, length: int, digits: int, hyphens: int) -> bool:
    return (length <= 12) and (digits == 0) and (hyphens == 0)

def niche_bonus(domain: str, niches) -> int:
    d = domain.lower()
    score = 0
    for niche, kws in niches.get("keywords", {}).items():
        if any(k in d for k in kws):
            score += niches.get("weights", {}).get(niche, 0)
    return score

def compute_score_row(domain: str, rules, wayback_pts: float, age_years: int) -> float:
    name, tld, length, hyphens, digits = base_features(domain)
    score = 0.0
    score += rules.get("tlds_preference", {}).get(tld, 0)
    # pénalités
    if length > rules["length_penalty"]["threshold"]:
        score -= rules["length_penalty"]["penalty"]
    if hyphens > 0:
        score -= rules.get("hyphen_penalty", 5)
    # brandabilité
    if brandable(name, length, digits, hyphens):
        score += rules.get("brand_bonus", 5)
    # Wayback & âge
    score += wayback_pts
    score += age_years * rules.get("rdap_age_weight", 2)
    return score

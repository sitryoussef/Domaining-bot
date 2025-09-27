import argparse, pandas as pd, time
from src.notifiers.discord_webhook import send_discord_message
from src.enrichers.wayback import wayback_snapshot_score
from src.enrichers.rdap import rdap_age_years
from src.scoring.core import load_rules, load_niches, compute_score_row, niche_bonus

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", required=True)
    ap.add_argument("--niches", required=True)
    ap.add_argument("--infile", required=True)   # data/expired.csv
    ap.add_argument("--out", required=True)      # reports/scan.csv
    args = ap.parse_args()

    rules = load_rules(args.rules)
    niches = load_niches(args.niches)

    df = pd.read_csv(args.infile)
    # On attend une colonne 'Domain' dans le CSV
    rows = []
    for _, r in df.iterrows():
        domain = str(r.get("Domain") or r.get("domain") or "").strip()
        if not domain or "." not in domain:
            continue
        wb = wayback_snapshot_score(domain)
        age = rdap_age_years(domain)
        sc = compute_score_row(domain, rules, wb, age) + niche_bonus(domain, niches)
        rows.append({
            "Domain": domain,
            "WaybackPts": round(wb,2),
            "AgeYears": age,
            "Score": round(sc,2)
        })

    out = pd.DataFrame(rows).sort_values("Score", ascending=False)
    out_top = out.head(10)
    out.to_csv(args.out, index=False)

    # Discord résumé
    lines = [f"**Top domaines ({time.strftime('%Y-%m-%d %H:%M')})**"]
    for _, rr in out_top.iterrows():
        lines.append(f"- `{rr['Domain']}` | Score **{rr['Score']}** | WB {rr['WaybackPts']} | Age {rr['AgeYears']}y")
    send_discord_message("\n".join(lines))

if __name__ == "__main__":
    main()

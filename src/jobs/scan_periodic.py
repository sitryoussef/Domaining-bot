import argparse
import os
import time
import pandas as pd

from src.notifiers.discord_webhook import send_discord_message
from src.enrichers.wayback import wayback_snapshot_score
from src.enrichers.rdap import rdap_age_years
from src.scoring.core import load_rules, load_niches, compute_score_row, niche_bonus


def _ensure_parent_dir(path: str) -> None:
    """Crée le dossier parent si nécessaire (ex: reports/)."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _read_csv_safe(path: str) -> pd.DataFrame:
    """Lecture CSV tolérante (UTF-8/UTF-8-SIG) + normalisation colonnes."""
    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8-sig")
    # normaliser noms de colonnes
    df.columns = [c.strip() for c in df.columns]
    # si la colonne Domain n'existe pas, essayer variantes
    if "Domain" not in df.columns:
        for alt in ("domain", "domains", "Domain Name", "name"):
            if alt in df.columns:
                df = df.rename(columns={alt: "Domain"})
                break
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", required=True)
    ap.add_argument("--niches", required=True)
    ap.add_argument("--infile", required=True)    # ex: data/expired.csv
    ap.add_argument("--out", required=True)       # ex: reports/scan.csv
    args = ap.parse_args()

    # Charger règles & niches
    rules = load_rules(args.rules)
    niches = load_niches(args.niches)

    # Lire les données
    if not os.path.exists(args.infile):
        send_discord_message(f"⚠️ Fichier introuvable: `{args.infile}`")
        raise SystemExit(1)

    df = _read_csv_safe(args.infile)

    if df.empty:
        send_discord_message("ℹ️ CSV vide — rien à scorer aujourd’hui.")
        # on écrit quand même un CSV vide pour le run
        _ensure_parent_dir(args.out)
        pd.DataFrame(columns=["Domain", "WaybackPts", "AgeYears", "Score"]).to_csv(args.out, index=False)
        return

    if "Domain" not in df.columns:
        send_discord_message("❌ Colonne `Domain` manquante dans le CSV.")
        raise SystemExit(1)

    rows = []
    # itérer de façon sûre
    for _, r in df.iterrows():
        domain = str(r.get("Domain") or "").strip()
        if not domain or "." not in domain:
            continue
        try:
            wb = float(wayback_snapshot_score(domain))
        except Exception:
            wb = 0.0
        try:
            age = int(rdap_age_years(domain))
        except Exception:
            age = 0

        try:
            sc = compute_score_row(domain, rules, wb, age) + niche_bonus(domain, niches)
        except Exception:
            sc = 0.0

        rows.append({
            "Domain": domain,
            "WaybackPts": round(wb, 2),
            "AgeYears": int(age),
            "Score": round(float(sc), 2)
        })

    if not rows:
        send_discord_message("ℹ️ Aucun domaine valide après filtrage.")
        _ensure_parent_dir(args.out)
        pd.DataFrame(columns=["Domain", "WaybackPts", "AgeYears", "Score"]).to_csv(args.out, index=False)
        return

    out = pd.DataFrame(rows).sort_values("Score", ascending=False)
    out_top = out.head(10)

    # S'assurer que le dossier de sortie existe (corrige ton erreur)
    _ensure_parent_dir(args.out)
    out.to_csv(args.out, index=False)

    # Discord résumé
    ts = time.strftime('%Y-%m-%d %H:%M')
    if out_top.empty:
        send_discord_message(f"ℹ️ {ts} — aucun domaine au-dessus du seuil.")
        return

    lines = [f"**Top domaines ({ts})**"]
    for _, rr in out_top.iterrows():
        lines.append(
            f"- `{rr['Domain']}` | Score **{rr['Score']}** | WB {rr['WaybackPts']} | Age {rr['AgeYears']}y"
        )
    send_discord_message("\n".join(lines))


if __name__ == "__main__":
    main()
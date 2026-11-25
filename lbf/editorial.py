"""Contrôle éditorial automatique. Produit une décision exploitable : pass / needs_review / rejected.
Il automatise des contrôles ; il ne remplace pas une analyse juridique complète."""
from __future__ import annotations

import re

ALLOWED_CLAIMS = {"fiction_satirique", "fait_public", "citation_exacte", "incertain"}

# Termes qui imposent une revue humaine (accusation, délit, groupes protégés, vote).
REVIEW_PATTERNS = [
    r"\bcondamn", r"\bpro(c|cè)s\b", r"\bmis en examen", r"\bdétourn", r"\bcorrupt", r"\bescroc", r"\bvol(e|eur)\b",
    r"\bfraude", r"\bemploi(s)? fictif", r"\bjuge\b", r"\btribunal",
    r"\bimmigr", r"\bmigrant", r"\bmusulman", r"\bislam", r"\bjui(f|ve)", r"\barabe", r"\bnoir(s)?\b", r"\bétranger",
    r"\breligi", r"\bhandicap", r"\bhomo", r"\btrans\b", r"\bgay\b",
    r"\bvotez\b", r"\bvote(z)? pour\b", r"\bne votez pas", r"\bbureau de vote", r"\bdate du scrutin",
    r"\ba déclaré\b", r"\ba dit que\b", r"\bselon (lui|elle)\b",
]
HARD_BLOCK = [r"\badresse personnelle\b", r"\bnuméro de téléphone\b", r"\btuer\b", r"\bharcel"]


def check(ep: dict) -> dict:
    issues, review, block = [], [], []
    segs = ep.get("narration_segments", [])
    words = sum(len(s["text"].split()) for s in segs)
    lo, hi = (50, 85) if ep.get("length", "court") == "court" else (70, 140)
    if (ep.get("narration_segments") or [{}])[0].get("role") == "teaser":
        hi += 10   # accroche v3 : le teaser d'ouverture (≤ 10 mots) s'ajoute au format habituel
    if not lo <= words <= hi:
        issues.append(f"Nombre de mots hors cible : {words} ({lo}–{hi})")
    text_all = " ".join(s["text"] for s in segs) + " " + ep.get("caption", "")
    for s in segs:
        ct = s.get("claim_type")
        if ct not in ALLOWED_CLAIMS:
            block.append(f"{s['id']} : claim_type manquant ou invalide")
        elif ct in ("fait_public", "citation_exacte"):
            if not ep.get("sources"):
                block.append(f"{s['id']} : {ct} sans source")
        elif ct == "incertain":
            review.append(f"{s['id']} : passage incertain")
    for pat in REVIEW_PATTERNS:
        if re.search(pat, text_all, re.IGNORECASE):
            review.append(f"Motif sensible détecté : {pat}")
    for pat in HARD_BLOCK:
        if re.search(pat, text_all, re.IGNORECASE):
            block.append(f"Motif interdit : {pat}")
    # Pas de mention à l'écran (décision du propriétaire) : la fiction doit donc être évidente par le contenu.
    if re.search(r"«[^»]{3,}»", text_all) and not ep.get("sources"):
        for s in segs:
            if "«" in s["text"] and s.get("claim_type") == "citation_exacte":
                block.append(f"{s['id']} : citation entre guillemets sans source")
    if not ep.get("cta_primary"):
        block.append("CTA principal absent")
    if not ep.get("cta_commercial"):
        issues.append("CTA commercial absent")
    if re.search(r"\bdemain\b", text_all, re.IGNORECASE) and not ep.get("next_episode_ready"):
        review.append("« demain » promis alors que l'épisode suivant n'est pas prêt")
    decision = "rejected" if block else ("needs_review" if review else "pass")
    return {"decision": decision, "word_count": words, "blocking": block, "review": review, "notes": issues}

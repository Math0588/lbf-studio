"""Test de rentabilité de la boutique à la demande, AVANT lancement (aucune dépense).

Modèle Spreadshop : la plateforme fixe un prix de base (fabrication, livraison standard, paiement, SAV) et TU
ajoutes ta marge ; elle encaisse et te reverse la marge. Pas de stock, pas d'avance : chaque vente est rentable
par construction. La seule vraie question est le VOLUME selon le prix → protocole ci-dessous.

Usage : python -m lbf.pricing <prix_de_base_spreadshop> [marges candidates…]
Le prix de base se lit dans ton tableau de bord Spreadshop au moment de créer le produit (il varie selon le
modèle de t-shirt et la technique d'impression) : ne jamais le deviner."""
from __future__ import annotations

import sys


def table(base: float, margins=(5, 8, 10, 12, 15)) -> list[dict]:
    rows = []
    for m in margins:
        price = round(base + m, 2)
        rows.append({"prix_client": price, "marge": m, "marge_pct": round(100 * m / price, 1),
                     # ventes nécessaires pour 100 € de recettes créateur
                     "ventes_pour_100eur": round(100 / m, 1)})
    return rows


PROTOCOLE = """
Protocole de test sans dépense (14 jours, uniquement des données réelles) :
1. Mettre en ligne 2 t-shirts « du gag » (ex. EXCELLENTE QUESTION., LE PAYS BUGUE.) avec une marge de 8 €.
2. Semaine 1 : marge 8 €. Semaine 2 : marge 12 € (même produits, mêmes CTA dans les vidéos).
3. Relever dans Spreadshop : visites de la boutique, commandes, marge encaissée. Saisir chaque semaine dans le
   tableau de bord (Boutique). Comparer marge totale / 1 000 vues de la semaine, pas les ventes seules.
4. Garder le prix qui maximise la marge totale ; ajouter de nouveaux designs seulement pour les gags qui marchent.
5. Commander UN échantillon (≈ 25–35 €, seule dépense, facultative mais recommandée) avant de pousser la boutique
   en story épinglée, pour vérifier la qualité réelle.
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print(PROTOCOLE)
        sys.exit(0)
    base = float(sys.argv[1].replace(",", "."))
    ms = [float(x) for x in sys.argv[2:]] or [5, 8, 10, 12, 15]
    print(f"Prix de base Spreadshop : {base:.2f} €")
    print(f"{'Prix client':>12} {'Marge':>7} {'Marge %':>8} {'Ventes/100 €':>13}")
    for r in table(base, ms):
        print(f"{r['prix_client']:>11.2f}€ {r['marge']:>6.2f}€ {r['marge_pct']:>7.1f}% {r['ventes_pour_100eur']:>13}")
    print(PROTOCOLE)

"""Compare les résultats des requêtes SANS et AVEC inférence et
écrit un rapport Markdown dans docs/comparaison_inference.md.

Usage : python compare_inference.py
"""
from rdflib import Literal

from kb import KnowledgeBase, iri, to_json
from reasoner import RULES

PARAMS = {
    "q1_sites": {},
    "q2_unesco": {"avant": Literal(2000)},
    "q3_stats_regions": {},
    "q4_hebergements": {"prixMax": Literal(1000)},
    "q5_guides": {},
    "q6_top_sites": {"noteMin": Literal(4)},
    "q7_sites_non_visites": {},
    "q8_budget_touriste": {},
}

EXPLICATIONS = {
    "q1_sites": "Sans inférence, seuls Matmata et Sidi Bou Saïd sont déclarés directement `tt:SiteTouristique`. "
                "Avec rdfs9 (subClassOf) et rdfs2 (domain de tt:prixEntree), musées, médinas, plages, etc. deviennent des sites touristiques.",
    "q2_unesco": "La classe `tt:SitePatrimoineMondial` n'a aucune instance déclarée : elle est entièrement remplie par la règle R2.",
    "q3_stats_regions": "Nécessite rdfs7 (situeDansVille ⊑ localiseDans), R1 (transitivité site→ville→région) "
                        "et rdfs3 (les régions sont typées `tt:Region` par le range de villeDeRegion).",
    "q4_hebergements": "Hôtels et maisons d'hôtes ne sont typés que par leur sous-classe ; rdfs9 les rend `tt:Hebergement`.",
    "q5_guides": "G3 et G4 n'ont pas de type : rdfs3 (range de tt:guidePar) les rend `tt:Guide`.",
    "q6_top_sites": "Les avis ne sont pas typés : rdfs2 (domain de tt:auteur, tt:concerne, tt:note) les rend `tt:Avis`.",
    "q7_sites_non_visites": "Même effet que Q1 : sans inférence, la négation ne porte que sur les 2 sites typés "
                            "directement (Matmata n'est pas visité). Avec inférence on trouve aussi Kerkouane, Ichkeul et 2 plages.",
    "q8_budget_touriste": "Les touristes sont typés par rdfs2 (domain de participeA) et les montants sont lus via la "
                          "super-propriété `tt:prix` (rdfs7 sur prixEntree et tarifVisite).",
}


def main():
    kb = KnowledgeBase()
    out = ["# Comparaison des résultats avec et sans inférence\n"]
    out.append(f"- Triplets bruts : **{len(kb.raw)}**")
    out.append(f"- Triplets après inférence : **{len(kb.inferred)}** "
               f"(+{len(kb.inferred) - len(kb.raw)}, point fixe atteint en {kb.iterations} itérations)\n")

    out.append("## Triplets inférés par règle\n")
    out.append("| Règle | Description | Triplets inférés |")
    out.append("|---|---|---|")
    for name, count in kb.rule_counts.items():
        out.append(f"| `{name}` | {RULES[name]['description']} | {count} |")

    out.append("\n## Exemples de triplets inférés\n")
    for name in kb.rule_counts:
        examples = [t for t, r in kb.provenance.items() if r == name][:3]
        if examples:
            out.append(f"**{name}**")
            for s, p, o in examples:
                out.append(f"- `{to_json(s)} {to_json(p)} {to_json(o)}`")
            out.append("")

    out.append("## Résultats des requêtes\n")
    out.append("| Requête | Sans inférence | Avec inférence | Explication |")
    out.append("|---|---|---|---|")
    for name, params in PARAMS.items():
        without = len(kb.run(name, inference=False, **params))
        with_ = len(kb.run(name, inference=True, **params))
        out.append(f"| {name} | {without} | {with_} | {EXPLICATIONS[name]} |")

    report = "\n".join(out) + "\n"
    (kb_dir := __import__("pathlib").Path(__file__).parent / "docs").mkdir(exist_ok=True)
    (kb_dir / "comparaison_inference.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()

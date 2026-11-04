"""
Moteur d'inférence RDFS (chaînage avant) écrit en SPARQL CONSTRUCT.

Chaque règle est une requête CONSTRUCT. On les applique en boucle jusqu'au
point fixe (plus aucun nouveau triplet). Pour chaque triplet inféré on garde
la règle qui l'a produit, ce qui permet de présenter les données inférées.

Règles RDFS standard (W3C RDF Semantics, §9.2) :
  rdfs2  domain          rdfs3  range
  rdfs5  subPropertyOf transitif
  rdfs7  héritage des propriétés
  rdfs9  héritage des types (subClassOf)
  rdfs11 subClassOf transitif
Règles métier :
  R1  tt:localiseDans est transitive (site -> ville -> région)
  R2  un site ayant une année d'inscription UNESCO est un tt:SitePatrimoineMondial
"""
from rdflib import Graph

PREFIXES = """
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX tt:   <http://example.org/tourisme-tunisie#>
"""

RULES = {
    "rdfs2_domain": {
        "description": "Si p rdfs:domain C et s p o, alors s rdf:type C",
        "query": "CONSTRUCT { ?s a ?c } WHERE { ?p rdfs:domain ?c . ?s ?p ?o . }",
    },
    "rdfs3_range": {
        "description": "Si p rdfs:range C et s p o (o ressource), alors o rdf:type C",
        "query": "CONSTRUCT { ?o a ?c } WHERE { ?p rdfs:range ?c . ?s ?p ?o . FILTER(isIRI(?o) || isBlank(?o)) }",
    },
    "rdfs5_subPropertyOf_transitif": {
        "description": "Si p subPropertyOf q et q subPropertyOf r, alors p subPropertyOf r",
        "query": "CONSTRUCT { ?p rdfs:subPropertyOf ?r } WHERE { ?p rdfs:subPropertyOf ?q . ?q rdfs:subPropertyOf ?r . FILTER(?p != ?r) }",
    },
    "rdfs7_subPropertyOf": {
        "description": "Si p subPropertyOf q et s p o, alors s q o",
        "query": "CONSTRUCT { ?s ?q ?o } WHERE { ?p rdfs:subPropertyOf ?q . ?s ?p ?o . }",
    },
    "rdfs9_subClassOf": {
        "description": "Si C subClassOf D et x rdf:type C, alors x rdf:type D",
        "query": "CONSTRUCT { ?x a ?d } WHERE { ?c rdfs:subClassOf ?d . ?x a ?c . }",
    },
    "rdfs11_subClassOf_transitif": {
        "description": "Si C subClassOf D et D subClassOf E, alors C subClassOf E",
        "query": "CONSTRUCT { ?c rdfs:subClassOf ?e } WHERE { ?c rdfs:subClassOf ?d . ?d rdfs:subClassOf ?e . FILTER(?c != ?e) }",
    },
    "R1_localiseDans_transitif": {
        "description": "Règle métier : si x localiseDans y et y localiseDans z, alors x localiseDans z",
        "query": "CONSTRUCT { ?x tt:localiseDans ?z } WHERE { ?x tt:localiseDans ?y . ?y tt:localiseDans ?z . FILTER(?x != ?z) }",
    },
    "R2_patrimoine_mondial": {
        "description": "Règle métier : un site avec une année d'inscription UNESCO est un tt:SitePatrimoineMondial",
        "query": "CONSTRUCT { ?s a tt:SitePatrimoineMondial } WHERE { ?s tt:anneeInscriptionUnesco ?annee . }",
    },
}


def apply_inference(base: Graph, rules=None):
    """Retourne (graphe enrichi, {triplet: règle}, {règle: nb triplets})."""
    g = Graph()
    for prefix, ns in base.namespaces():
        g.bind(prefix, ns)
    for t in base:
        g.add(t)

    selected = {k: v for k, v in RULES.items() if rules is None or k in rules}
    provenance = {}
    iterations = 0
    while True:
        iterations += 1
        new_this_round = 0
        for name, rule in selected.items():
            for triple in g.query(PREFIXES + rule["query"]):
                if triple not in g:
                    g.add(triple)
                    provenance[triple] = name
                    new_this_round += 1
        if new_this_round == 0:
            break

    counts = {name: 0 for name in selected}
    for rule_name in provenance.values():
        counts[rule_name] += 1
    return g, provenance, counts, iterations

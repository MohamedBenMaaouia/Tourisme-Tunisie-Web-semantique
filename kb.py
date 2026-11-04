"""Chargement de la base de connaissance et exécution des requêtes SPARQL."""
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import XSD

from reasoner import apply_inference

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
QUERY_DIR = BASE_DIR / "queries"
TT = "http://example.org/tourisme-tunisie#"
PREFIXES = {
    TT: "tt",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://xmlns.com/foaf/0.1/": "foaf",
    "http://www.w3.org/2003/01/geo/wgs84_pos#": "geo",
    "http://www.w3.org/2001/XMLSchema#": "xsd",
}


class KnowledgeBase:
    def __init__(self):
        self.raw = Graph()
        self.raw.bind("tt", TT)
        for f in ("schema.ttl", "donnees.ttl"):
            self.raw.parse(DATA_DIR / f, format="turtle")
        self.inferred, self.provenance, self.rule_counts, self.iterations = apply_inference(self.raw)
        self.queries = {p.stem: p.read_text(encoding="utf-8") for p in sorted(QUERY_DIR.glob("*.rq"))}

    def graph(self, inference: bool) -> Graph:
        return self.inferred if inference else self.raw

    def run(self, name: str, inference: bool = True, **params):
        """Exécute une requête nommée. Les paramètres sont passés par initBindings
        (valeurs typées, aucune concaténation de chaînes => pas d'injection SPARQL)."""
        bindings = {k: v for k, v in params.items() if v is not None}
        result = self.graph(inference).query(self.queries[name], initBindings=bindings)
        rows = []
        for row in result:
            item = {}
            for var in result.vars:
                item[str(var)] = to_json(row[var])
            rows.append(item)
        return rows


def to_json(term):
    if term is None:
        return None
    if isinstance(term, URIRef):
        s = str(term)
        for ns, prefix in PREFIXES.items():
            if s.startswith(ns):
                return prefix + ":" + s[len(ns):]
        return s
    if isinstance(term, Literal):
        value = term.toPython()
        if term.datatype == XSD.decimal or isinstance(value, float):
            return round(float(value), 2)
        if isinstance(value, (int, bool, str)):
            return value
        return str(term)
    return str(term)


def iri(local_name: str) -> URIRef:
    return URIRef(TT + local_name)


def lit(value, datatype):
    return Literal(value, datatype=datatype)

"""
Web service REST : Tourisme en Tunisie
Expose les résultats des requêtes SPARQL en JSON.

Tous les endpoints acceptent ?inference=true|false (true par défaut) pour
interroger le graphe enrichi ou le graphe brut.

Lancement : python app.py   ->   http://localhost:5000
"""
import unicodedata

from flask import Flask, jsonify, request
from rdflib import Literal
from rdflib.namespace import XSD
from werkzeug.exceptions import HTTPException

from kb import KnowledgeBase, iri, to_json
from reasoner import RULES
from validation import ApiError, get_bool, get_choice, get_float, get_int, get_pattern

app = Flask(__name__)
app.json.ensure_ascii = False   # accents lisibles dans le JSON
app.json.sort_keys = False

kb = KnowledgeBase()

SITE_TYPES = {
    "archeologique": "SiteArcheologique",
    "musee": "Musee",
    "medina": "Medina",
    "plage": "Plage",
    "naturel": "SiteNaturel",
    "unesco": "SitePatrimoineMondial",
}


# ------------------------------------------------------------------ helpers

def normalize(text: str) -> str:
    """minuscules sans accents : 'Béja' -> 'beja'"""
    return "".join(c for c in unicodedata.normalize("NFD", text.lower())
                   if unicodedata.category(c) != "Mn").strip()


def known_regions():
    q = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
           PREFIX tt: <http://example.org/tourisme-tunisie#>
           SELECT DISTINCT ?nom WHERE { ?v tt:villeDeRegion ?r . ?r rdfs:label ?nom }"""
    return sorted(str(r.nom) for r in kb.raw.query(q))


def resolve_region(args):
    raw = args.get("region")
    if not raw:
        return None
    regions = known_regions()
    for name in regions:
        if normalize(name) == normalize(raw):
            return Literal(name)
    raise ApiError(404, f"Région inconnue : '{raw}'.", {"regions_disponibles": regions})


def respond(query_name, inference, params, results, **extra):
    body = {
        "requete": query_name,
        "inference": inference,
        "parametres": {k: to_json(v) for k, v in params.items() if v is not None},
        "nombre_resultats": len(results),
        **extra,
        "resultats": results,
    }
    return jsonify(body)


def run(query_name, **params):
    inference = get_bool(request.args, "inference", default=True)
    results = kb.run(query_name, inference=inference, **params)
    return respond(query_name, inference, params, results)


# ------------------------------------------------------------------ endpoints

@app.get("/")
def index():
    return jsonify({
        "service": "API Tourisme en Tunisie (RDF / RDFS / SPARQL)",
        "parametre_commun": "inference=true|false (défaut : true)",
        "endpoints": {
            "GET /api/sites": "Catalogue des sites. Filtres : type (archeologique|musee|medina|plage|naturel|unesco), region",
            "GET /api/sites/unesco": "Sites UNESCO inscrits jusqu'à une année. Param : avant (défaut 2100)",
            "GET /api/sites/top": "Sites les mieux notés. Param : note_min (1-5, défaut 4)",
            "GET /api/sites/non-visites": "Sites absents de toute visite guidée",
            "GET /api/regions/stats": "Nombre de sites et prix moyen par région",
            "GET /api/hebergements": "Hébergements. Filtres : region, etoiles_min (1-5), prix_max",
            "GET /api/guides": "Guides et activité. Filtre : langue (code ISO, ex. fr)",
            "GET /api/touristes/budget": "Budget de chaque touriste",
            "GET /api/touristes/<id>/budget": "Budget d'un touriste (ex. T1)",
            "GET /api/inference/regles": "Triplets inférés par règle. Params : regle, limit",
            "GET /api/inference/comparaison": "Nombre de résultats de chaque requête avec / sans inférence",
        },
    })


@app.get("/api/sites")
def sites():
    type_key = get_choice(request.args, "type", SITE_TYPES)
    params = {
        "typeFiltre": iri(SITE_TYPES[type_key]) if type_key else None,
        "regionNom": resolve_region(request.args),
    }
    return run("q1_sites", **params)


@app.get("/api/sites/unesco")
def sites_unesco():
    avant = get_int(request.args, "avant", default=2100, minimum=1972, maximum=2100)
    return run("q2_unesco", avant=Literal(avant, datatype=XSD.integer))


@app.get("/api/sites/top")
def sites_top():
    note_min = get_float(request.args, "note_min", default=4.0, minimum=1, maximum=5)
    return run("q6_top_sites", noteMin=Literal(note_min, datatype=XSD.decimal))


@app.get("/api/sites/non-visites")
def sites_non_visites():
    return run("q7_sites_non_visites")


@app.get("/api/regions/stats")
def regions_stats():
    return run("q3_stats_regions")


@app.get("/api/hebergements")
def hebergements():
    etoiles = get_int(request.args, "etoiles_min", minimum=1, maximum=5)
    prix_max = get_float(request.args, "prix_max", default=100000, minimum=0)
    params = {
        "prixMax": Literal(prix_max, datatype=XSD.decimal),
        "etoilesMin": Literal(etoiles, datatype=XSD.integer) if etoiles else None,
        "regionNom": resolve_region(request.args),
    }
    return run("q4_hebergements", **params)


@app.get("/api/guides")
def guides():
    langue = get_pattern(request.args, "langue", r"[a-z]{2}", "code langue à 2 lettres, ex. fr")
    return run("q5_guides", langue=Literal(langue) if langue else None)


@app.get("/api/touristes/budget")
def budgets():
    return run("q8_budget_touriste")


@app.get("/api/touristes/<touriste_id>/budget")
def budget(touriste_id):
    if not touriste_id.isalnum():
        raise ApiError(400, "Identifiant de touriste invalide.")
    uri = iri(touriste_id)
    if (uri, None, None) not in kb.raw:
        raise ApiError(404, f"Touriste '{touriste_id}' introuvable.")
    response = run("q8_budget_touriste", touriste=uri)
    if not response.get_json()["resultats"] and get_bool(request.args, "inference"):
        raise ApiError(404, f"Aucune visite enregistrée pour '{touriste_id}'.")
    return response


@app.get("/api/inference/regles")
def inference_rules():
    rule = request.args.get("regle")
    if rule and rule not in RULES:
        raise ApiError(400, f"Règle inconnue : '{rule}'.", {"regles": list(RULES)})
    limit = get_int(request.args, "limit", default=5, minimum=1, maximum=500)
    selected = [rule] if rule else list(RULES)
    rules = []
    for name in selected:
        triples = [t for t, r in kb.provenance.items() if r == name]
        rules.append({
            "regle": name,
            "description": RULES[name]["description"],
            "nombre_triplets_inferes": len(triples),
            "exemples": [{"sujet": to_json(s), "predicat": to_json(p), "objet": to_json(o)}
                         for s, p, o in triples[:limit]],
        })
    return jsonify({
        "triplets_bruts": len(kb.raw),
        "triplets_apres_inference": len(kb.inferred),
        "triplets_inferes": len(kb.inferred) - len(kb.raw),
        "iterations_point_fixe": kb.iterations,
        "regles": rules,
    })


@app.get("/api/inference/comparaison")
def inference_comparison():
    defaults = {
        "q2_unesco": {"avant": Literal(2100)},
        "q4_hebergements": {"prixMax": Literal(100000)},
        "q6_top_sites": {"noteMin": Literal(4)},
    }
    rows = []
    for name in kb.queries:
        p = defaults.get(name, {})
        without = len(kb.run(name, inference=False, **p))
        with_ = len(kb.run(name, inference=True, **p))
        rows.append({"requete": name, "sans_inference": without, "avec_inference": with_,
                     "gain": with_ - without})
    return jsonify({"triplets_bruts": len(kb.raw), "triplets_apres_inference": len(kb.inferred),
                    "requetes": rows})


# ------------------------------------------------------------------ erreurs

@app.errorhandler(ApiError)
def handle_api_error(err):
    body = {"erreur": {"code": err.status, "message": err.message}}
    if err.details:
        body["erreur"]["details"] = err.details
    return jsonify(body), err.status


@app.errorhandler(HTTPException)
def handle_http_error(err):
    return jsonify({"erreur": {"code": err.code, "message": err.description}}), err.code


@app.errorhandler(Exception)
def handle_unexpected(err):
    app.logger.exception(err)
    return jsonify({"erreur": {"code": 500, "message": "Erreur interne du serveur."}}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)

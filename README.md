# Tourisme en Tunisie : base de connaissance RDF + web service SPARQL

Projet de web sémantique : vocabulaire RDFS, données RDF (Turtle), requêtes SPARQL,
inférence RDFS et web service REST (Flask + rdflib) qui renvoie du JSON.

## Installation et lancement

```bash
pip install -r requirements.txt
python app.py                  # http://localhost:5000  (liste des endpoints sur /)
python compare_inference.py    # régénère docs/comparaison_inference.md
python -m pytest -q            # 17 tests du web service
```

## Structure

| Fichier | Rôle |
|---|---|
| `data/schema.ttl` | Vocabulaire RDFS : 17 classes, 20 propriétés, hiérarchies subClassOf / subPropertyOf, domain / range, réutilisation FOAF, W3C Geo, Dublin Core |
| `data/donnees.ttl` | Instances : 16 sites, 8 hébergements, 4 guides, 6 touristes, 6 visites, 12 avis |
| `queries/q1…q8.rq` | Les 8 requêtes SPARQL, commentées |
| `reasoner.py` | Moteur d'inférence : règles RDFS (rdfs2, 3, 5, 7, 9, 11) et règles métier R1, R2 en SPARQL CONSTRUCT, jusqu'au point fixe |
| `kb.py` | Charge le graphe brut et le graphe inféré, exécute les requêtes avec des paramètres typés (`initBindings`) |
| `validation.py` | Validation des paramètres HTTP et erreurs JSON |
| `app.py` | Web service REST |
| `compare_inference.py` | Rapport avec / sans inférence |
| `docs/schema_classes.png` | Schéma simplifié de la hiérarchie des classes (version présentation) |
| `docs/schema.png` | Schéma complet du modèle, classes et propriétés (source : `schema.dot`, Graphviz) |
| `docs/comparaison_inference.md` | Résultat de la comparaison |

## Endpoints (tous en GET, tous acceptent `?inference=true|false`)

| Endpoint | Requête | Paramètres |
|---|---|---|
| `/api/sites` | Q1 | `type` (archeologique, musee, medina, plage, naturel, unesco), `region` |
| `/api/sites/unesco` | Q2 | `avant` (année) |
| `/api/regions/stats` | Q3 | — |
| `/api/hebergements` | Q4 | `region`, `etoiles_min`, `prix_max` |
| `/api/guides` | Q5 | `langue` (ex. `fr`) |
| `/api/sites/top` | Q6 | `note_min` (1 à 5) |
| `/api/sites/non-visites` | Q7 | — |
| `/api/touristes/budget`, `/api/touristes/<id>/budget` | Q8 | — |
| `/api/inference/regles` | triplets inférés | `regle`, `limit` |
| `/api/inference/comparaison` | sans / avec inférence | — |

Erreurs : `400` paramètre invalide, `404` région / touriste / route inconnus, `500` erreur interne,
toujours au format `{"erreur": {"code": …, "message": …, "details": …}}`.

## Inférence

Les données ne déclarent que le type le plus précis, et villes, régions, touristes, visites
et avis n'ont pas de type : ce sont les règles qui les déduisent.

- **rdfs2 / rdfs3** : typage par `rdfs:domain` / `rdfs:range` (ex. `tt:G3` devient `tt:Guide` via `tt:guidePar`)
- **rdfs7 / rdfs5** : héritage des propriétés (`tt:prixNuit` ⇒ `tt:prix`, `tt:situeDansVille` ⇒ `tt:localiseDans` ⇒ `geo:location`)
- **rdfs9 / rdfs11** : héritage des types (`tt:Hotel` ⇒ `tt:Hebergement` ⇒ `tt:Lieu` ⇒ `geo:SpatialThing`)
- **R1 (métier)** : `tt:localiseDans` est transitive (site → ville → région)
- **R2 (métier)** : un site avec `tt:anneeInscriptionUnesco` est un `tt:SitePatrimoineMondial`

439 triplets bruts → 818 après inférence. Les triplets RDFS produits ont été vérifiés avec
le raisonneur `owlrl` (tous présents dans sa fermeture RDFS).

## Données

Les 8 sites UNESCO et leurs années d'inscription sont réels. Les prix, hôtels, guides,
touristes, visites et avis sont des données d'exemple fictives.

## Usage de l'IA générative

Un outil d'IA générative a été utilisé comme assistant pour écrire le code, comme le
permet l'énoncé. Chaque partie a été relue et peut être expliquée lors de la soutenance.

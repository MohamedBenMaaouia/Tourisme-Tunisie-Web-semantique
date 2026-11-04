# Comparaison des résultats avec et sans inférence

- Triplets bruts : **439**
- Triplets après inférence : **818** (+379, point fixe atteint en 3 itérations)

## Triplets inférés par règle

| Règle | Description | Triplets inférés |
|---|---|---|
| `rdfs2_domain` | Si p rdfs:domain C et s p o, alors s rdf:type C | 87 |
| `rdfs3_range` | Si p rdfs:range C et s p o (o ressource), alors o rdf:type C | 10 |
| `rdfs5_subPropertyOf_transitif` | Si p subPropertyOf q et q subPropertyOf r, alors p subPropertyOf r | 2 |
| `rdfs7_subPropertyOf` | Si p subPropertyOf q et s p o, alors s q o | 132 |
| `rdfs9_subClassOf` | Si C subClassOf D et x rdf:type C, alors x rdf:type D | 94 |
| `rdfs11_subClassOf_transitif` | Si C subClassOf D et D subClassOf E, alors C subClassOf E | 22 |
| `R1_localiseDans_transitif` | Règle métier : si x localiseDans y et y localiseDans z, alors x localiseDans z | 24 |
| `R2_patrimoine_mondial` | Règle métier : un site avec une année d'inscription UNESCO est un tt:SitePatrimoineMondial | 8 |

## Exemples de triplets inférés

**rdfs2_domain**
- `tt:A5 rdf:type tt:Avis`
- `tt:PlageHammamet rdf:type tt:Lieu`
- `tt:VIS2 rdf:type tt:Visite`

**rdfs3_range**
- `tt:R_Bizerte rdf:type tt:Region`
- `tt:R_Tozeur rdf:type tt:Region`
- `tt:R_Mahdia rdf:type tt:Region`

**rdfs5_subPropertyOf_transitif**
- `tt:villeDeRegion rdfs:subPropertyOf geo:location`
- `tt:situeDansVille rdfs:subPropertyOf geo:location`

**rdfs7_subPropertyOf**
- `tt:MuseeSousse tt:prix 10.0`
- `tt:Ichkeul tt:prix 5.0`
- `tt:V_ElJem tt:localiseDans tt:R_Mahdia`

**rdfs9_subClassOf**
- `tt:R_Beja rdf:type tt:Lieu`
- `tt:ElJem rdf:type geo:SpatialThing`
- `tt:ChottElJerid rdf:type geo:SpatialThing`

**rdfs11_subClassOf_transitif**
- `tt:SiteNaturel rdfs:subClassOf tt:Lieu`
- `tt:Medina rdfs:subClassOf tt:Lieu`
- `tt:Ville rdfs:subClassOf geo:SpatialThing`

**R1_localiseDans_transitif**
- `tt:H_Oasis tt:localiseDans tt:R_Tozeur`
- `tt:MedinaTunis tt:localiseDans tt:R_Tunis`
- `tt:Ichkeul tt:localiseDans tt:R_Bizerte`

**R2_patrimoine_mondial**
- `tt:Carthage rdf:type tt:SitePatrimoineMondial`
- `tt:Dougga rdf:type tt:SitePatrimoineMondial`
- `tt:Ichkeul rdf:type tt:SitePatrimoineMondial`

## Résultats des requêtes

| Requête | Sans inférence | Avec inférence | Explication |
|---|---|---|---|
| q1_sites | 2 | 16 | Sans inférence, seuls Matmata et Sidi Bou Saïd sont déclarés directement `tt:SiteTouristique`. Avec rdfs9 (subClassOf) et rdfs2 (domain de tt:prixEntree), musées, médinas, plages, etc. deviennent des sites touristiques. |
| q2_unesco | 0 | 8 | La classe `tt:SitePatrimoineMondial` n'a aucune instance déclarée : elle est entièrement remplie par la règle R2. |
| q3_stats_regions | 0 | 10 | Nécessite rdfs7 (situeDansVille ⊑ localiseDans), R1 (transitivité site→ville→région) et rdfs3 (les régions sont typées `tt:Region` par le range de villeDeRegion). |
| q4_hebergements | 0 | 8 | Hôtels et maisons d'hôtes ne sont typés que par leur sous-classe ; rdfs9 les rend `tt:Hebergement`. |
| q5_guides | 2 | 4 | G3 et G4 n'ont pas de type : rdfs3 (range de tt:guidePar) les rend `tt:Guide`. |
| q6_top_sites | 0 | 7 | Les avis ne sont pas typés : rdfs2 (domain de tt:auteur, tt:concerne, tt:note) les rend `tt:Avis`. |
| q7_sites_non_visites | 1 | 5 | Même effet que Q1 : sans inférence, la négation ne porte que sur les 2 sites typés directement (Matmata n'est pas visité). Avec inférence on trouve aussi Kerkouane, Ichkeul et 2 plages. |
| q8_budget_touriste | 0 | 6 | Les touristes sont typés par rdfs2 (domain de participeA) et les montants sont lus via la super-propriété `tt:prix` (rdfs7 sur prixEntree et tarifVisite). |

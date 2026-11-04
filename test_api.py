"""Tests du web service : python -m pytest -q"""
import pytest

from app import app


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


def get(client, url, status=200):
    r = client.get(url)
    assert r.status_code == status, (url, r.get_json())
    return r.get_json()


def test_index(client):
    assert "endpoints" in get(client, "/")


def test_sites_with_and_without_inference(client):
    assert get(client, "/api/sites")["nombre_resultats"] == 16
    assert get(client, "/api/sites?inference=false")["nombre_resultats"] == 2


def test_sites_filters(client):
    musees = get(client, "/api/sites?type=musee")["resultats"]
    assert {s["site"] for s in musees} == {"tt:Bardo", "tt:MuseeSousse"}
    # recherche insensible aux accents
    beja = get(client, "/api/sites?region=beja")["resultats"]
    assert [s["site"] for s in beja] == ["tt:Dougga"]


def test_unesco(client):
    data = get(client, "/api/sites/unesco?avant=1980")
    assert data["nombre_resultats"] == 4
    assert get(client, "/api/sites/unesco?inference=false")["nombre_resultats"] == 0


def test_regions_and_top(client):
    stats = get(client, "/api/regions/stats")["resultats"]
    assert stats[0]["nomRegion"] == "Tunis" and stats[0]["nbSites"] == 4
    top = get(client, "/api/sites/top?note_min=5")["resultats"]
    assert all(s["noteMoyenne"] == 5 for s in top)


def test_hebergements(client):
    data = get(client, "/api/hebergements?etoiles_min=5")["resultats"]
    assert {h["hebergement"] for h in data} == {"tt:H_Jasmin", "tt:H_Djerba"}
    assert get(client, "/api/hebergements?prix_max=150")["nombre_resultats"] == 2


def test_guides_and_budget(client):
    assert get(client, "/api/guides?langue=de")["resultats"][0]["nom"] == "Karim Jaziri"
    t1 = get(client, "/api/touristes/T1/budget")["resultats"][0]
    assert t1["total"] == 188.0


def test_inference_endpoints(client):
    data = get(client, "/api/inference/regles?regle=R1_localiseDans_transitif&limit=2")
    assert len(data["regles"][0]["exemples"]) == 2
    comp = get(client, "/api/inference/comparaison")["requetes"]
    assert all(r["avec_inference"] >= r["sans_inference"] for r in comp)


@pytest.mark.parametrize("url,status", [
    ("/api/sites?type=chateau", 400),
    ("/api/sites?region=Paris", 404),
    ("/api/sites/unesco?avant=abc", 400),
    ("/api/sites/top?note_min=9", 400),
    ("/api/hebergements?etoiles_min=0", 400),
    ("/api/guides?langue=francais", 400),
    ("/api/sites?inference=peut-etre", 400),
    ("/api/touristes/T99/budget", 404),
    ("/api/inconnu", 404),
])
def test_errors(client, url, status):
    data = get(client, url, status)
    assert data["erreur"]["code"] == status

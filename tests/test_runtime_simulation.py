from __future__ import annotations


def test_healthz_is_healthy_by_default(client):
    response = client.get("/healthz")
    assert response.status_code == 200


def test_simulated_unhealthy_flips_healthz(client):
    enable = client.post("/__simulate/unhealthy")
    assert enable.status_code == 200

    unhealthy = client.get("/healthz")
    assert unhealthy.status_code == 503

    disable = client.post("/__simulate/healthy")
    assert disable.status_code == 200

    healthy_again = client.get("/healthz")
    assert healthy_again.status_code == 200

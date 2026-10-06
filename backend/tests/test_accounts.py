def test_create_and_list_account(client):
    response = client.post(
        "/api/v1/accounts",
        json={"name": "ACME Ltd.", "account_type": "musteri", "opening_balance": 1000},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "ACME Ltd."
    assert body["current_balance"] == 1000

    response = client.get("/api/v1/accounts")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_missing_account_returns_404(client):
    response = client.get("/api/v1/accounts/999")
    assert response.status_code == 404

from app import models, schemas


def test_get_all_transactions(test_user, logged_client, test_transactions):
    res = logged_client.get("/transactions/")
    assert res.status_code == 200
    user_transactions = [
        trans for trans in test_transactions if trans.user_id == test_user["id"]
    ]
    assert len(res.json()) == len(user_transactions)
    res_data = [schemas.Transaction(**trans) for trans in res.json()]


def test_get_all_transactions_unauthorized(client, test_transactions):
    res = client.get("/transactions/")
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


def test_get_one_transactions(logged_client, test_transactions):
    res = logged_client.get(f"/transactions/{test_transactions[0].id}")
    assert res.status_code == 200
    res_data = schemas.Transaction(**res.json())
    assert res_data.id == test_transactions[0].id


def test_get_one_transactions_not_allowed(test_users, logged_client, test_transactions):
    other_users_transactions = [
        trans for trans in test_transactions if trans.user_id != test_users[0]["id"]
    ]
    res = logged_client.get(f"/transactions/{other_users_transactions[0].id}")
    assert res.status_code == 403
    assert res.json().get("detail") == "Not allowed"


def test_get_one_transaction_non_existent(logged_client, test_transactions):
    res = logged_client.get("/transactions/123456")
    assert res.status_code == 404
    assert res.json().get("detail") == "Transaction was not found"


def test_update_transaction(logged_client, test_transactions):
    updated_trans = {
        "title": "new_title",
        "amount": 20000
    }
    res = logged_client.put(f"/transactions/{test_transactions[0].id}", json=updated_trans)
    assert res.status_code == 200
    new_trans = schemas.Transaction(**res.json())
    assert new_trans.id == test_transactions[0].id
    assert new_trans.title == updated_trans['title']
    assert new_trans.amount == updated_trans["amount"]


def test_update_transaction_title(logged_client, test_transactions):
    updated_trans = {
        "title": "new_title"
    }
    res = logged_client.put(f"/transactions/{test_transactions[0].id}", json=updated_trans)
    assert res.status_code == 200
    new_trans = schemas.Transaction(**res.json())
    assert new_trans.id == test_transactions[0].id
    assert new_trans.title == updated_trans['title']
    assert new_trans.amount == test_transactions[0].amount


def test_update_transaction_amount(logged_client, test_transactions):
    updated_trans = {
        "amount": 20000
    }
    res = logged_client.put(f"/transactions/{test_transactions[0].id}", json=updated_trans)
    assert res.status_code == 200
    new_trans = schemas.Transaction(**res.json())
    assert new_trans.id == test_transactions[0].id
    assert new_trans.title == test_transactions[0].title
    assert new_trans.amount == updated_trans['amount']


def test_update_transaction_validation_error(logged_client, test_transactions):
    updated_trans = {
        "title": "new_title",
        "amount": "new_amount"
    }
    res = logged_client.put(f"/transactions/{test_transactions[0].id}", json=updated_trans)
    assert res.status_code == 422


def test_update_transaction_non_existent(logged_client, test_transactions):
    updated_trans = {
        "title": "new_title",
        "amount": 20000
    }
    res = logged_client.put("/transactions/123456", json=updated_trans)
    assert res.status_code == 404
    assert res.json().get('detail') == "Transaction was not found"


def test_update_transaction_not_allowed(test_users, logged_client, test_transactions):
    other_users_transactions = [
        trans for trans in test_transactions if trans.user_id != test_users[0]["id"]
    ]
    updated_trans = {
        "title": "new_title",
        "amount": 20000
    }
    res = logged_client.put(f"/transactions/{other_users_transactions[0].id}", json=updated_trans)
    assert res.status_code == 403
    assert res.json().get('detail') == "Not allowed"


def test_delete_transaction(logged_client, test_transactions, db_session):
    res = logged_client.delete(f"/transactions/{test_transactions[0].id}")
    assert res.status_code == 204
    trans_query = db_session.query(models.Transaction).filter(models.Transaction.id == test_transactions[0].id)
    assert trans_query.first() == None


def test_delete_transaction_unauthorized(client, test_transactions):
    res = client.delete(f"/transactions/{test_transactions[0].id}")
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


def test_delete_transaction_non_existent(logged_client, test_transactions):
    res = logged_client.delete("/transactions/123456")
    assert res.status_code == 404
    assert res.json().get('detail') == "Transaction was not found"


def test_delete_transaction_not_allowed(test_users, logged_client, test_transactions):
    other_users_transactions = [
        trans for trans in test_transactions if trans.user_id != test_users[0]["id"]
    ]
    res = logged_client.delete(f"/transactions/{other_users_transactions[0].id}")
    assert res.status_code == 403
    assert res.json().get('detail') == "Not allowed"

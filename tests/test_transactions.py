from app import models, schemas


def test_create_transaction(logged_client, test_categories, test_accounts):
    transaction_data = {
        "title": "New Transaction",
        "amount": 1500.0,
        "category_id": test_categories[0].id,
        "account_id": test_accounts[0].id,
    }
    res = logged_client.post("/transactions/", json=transaction_data)
    assert res.status_code == 201
    new_transaction = schemas.Transaction(**res.json())
    assert new_transaction.title == transaction_data["title"]
    assert new_transaction.amount == transaction_data["amount"]
    assert new_transaction.category_id == transaction_data["category_id"]
    assert new_transaction.account_id == transaction_data["account_id"]


def test_create_transaction_missing_account_id(logged_client, test_categories):
    transaction_data = {
        "title": "Transaction without Account",
        "amount": 1500.0,
        "category_id": test_categories[0].id,
    }
    res = logged_client.post("/transactions/", json=transaction_data)
    assert res.status_code == 422


def test_create_transaction_invalid_account_id(logged_client, test_categories):
    transaction_data = {
        "title": "Transaction with Invalid Account",
        "amount": 1500.0,
        "category_id": test_categories[0].id,
        "account_id": 999999,  # Non-existent account
    }
    res = logged_client.post("/transactions/", json=transaction_data)
    assert res.status_code == 404
    assert res.json().get("detail") == "Account was not found"


def test_create_transaction_forbidden_account(
    test_users, logged_client, test_categories, test_accounts
):
    # Try to use another user's account
    other_user_account = None
    for acc in test_accounts:
        if acc.user_id != test_users[0]["id"]:
            other_user_account = acc
            break

    assert other_user_account is not None
    transaction_data = {
        "title": "Transaction with Forbidden Account",
        "amount": 1500.0,
        "category_id": test_categories[0].id,
        "account_id": other_user_account.id,
    }
    res = logged_client.post("/transactions/", json=transaction_data)
    assert res.status_code == 403
    assert res.json().get("detail") == "Not allowed"


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


def test_update_transaction(
    logged_client, test_transactions, test_categories, test_accounts
):
    updated_trans = {
        "title": "new_title",
        "amount": 20000,
        "category_id": test_categories[1].id,
        "account_id": test_accounts[0].id,
    }
    res = logged_client.put(
        f"/transactions/{test_transactions[0].id}", json=updated_trans
    )
    assert res.status_code == 200
    new_trans = schemas.Transaction(**res.json())
    assert new_trans.id == test_transactions[0].id
    assert new_trans.title == updated_trans["title"]
    assert new_trans.amount == updated_trans["amount"]
    assert new_trans.category_id == updated_trans["category_id"]
    assert new_trans.account_id == updated_trans["account_id"]


def test_update_transaction_title(logged_client, test_transactions):
    updated_trans = {"title": "new_title"}
    res = logged_client.put(
        f"/transactions/{test_transactions[0].id}", json=updated_trans
    )
    assert res.status_code == 200
    new_trans = schemas.Transaction(**res.json())
    assert new_trans.id == test_transactions[0].id
    assert new_trans.title == updated_trans["title"]
    assert new_trans.amount == test_transactions[0].amount
    assert new_trans.category_id == test_transactions[0].category_id
    assert new_trans.account_id == test_transactions[0].account_id


def test_update_transaction_amount(logged_client, test_transactions):
    updated_trans = {"amount": 20000}
    res = logged_client.put(
        f"/transactions/{test_transactions[0].id}", json=updated_trans
    )
    assert res.status_code == 200
    new_trans = schemas.Transaction(**res.json())
    assert new_trans.id == test_transactions[0].id
    assert new_trans.title == test_transactions[0].title
    assert new_trans.amount == updated_trans["amount"]
    assert new_trans.category_id == test_transactions[0].category_id
    assert new_trans.account_id == test_transactions[0].account_id


def test_update_transaction_validation_error(logged_client, test_transactions):
    updated_trans = {
        "title": "new_title",
        "amount": "new_amount",
        "category_id": "invalid_category_id",
    }
    res = logged_client.put(
        f"/transactions/{test_transactions[0].id}", json=updated_trans
    )
    assert res.status_code == 422


def test_update_transaction_non_existent(
    logged_client, test_transactions, test_categories, test_accounts
):
    updated_trans = {
        "title": "new_title",
        "amount": 20000,
        "category_id": test_categories[0].id,
        "account_id": test_accounts[0].id,
    }
    res = logged_client.put("/transactions/123456", json=updated_trans)
    assert res.status_code == 404
    assert res.json().get("detail") == "Transaction was not found"


def test_update_transaction_not_allowed(
    test_users, logged_client, test_transactions, test_categories, test_accounts
):
    other_users_transactions = [
        trans for trans in test_transactions if trans.user_id != test_users[0]["id"]
    ]
    updated_trans = {
        "title": "new_title",
        "amount": 20000,
        "category_id": test_categories[0].id,
        "account_id": test_accounts[0].id,
    }
    res = logged_client.put(
        f"/transactions/{other_users_transactions[0].id}", json=updated_trans
    )
    assert res.status_code == 403
    assert res.json().get("detail") == "Not allowed"


def test_delete_transaction(logged_client, test_transactions, db_session):
    res = logged_client.delete(f"/transactions/{test_transactions[0].id}")
    assert res.status_code == 204
    trans_query = db_session.query(models.Transaction).filter(
        models.Transaction.id == test_transactions[0].id
    )
    assert trans_query.first() == None


def test_delete_transaction_unauthorized(client, test_transactions):
    res = client.delete(f"/transactions/{test_transactions[0].id}")
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


def test_delete_transaction_non_existent(logged_client, test_transactions):
    res = logged_client.delete("/transactions/123456")
    assert res.status_code == 404
    assert res.json().get("detail") == "Transaction was not found"


def test_delete_transaction_not_allowed(test_users, logged_client, test_transactions):
    other_users_transactions = [
        trans for trans in test_transactions if trans.user_id != test_users[0]["id"]
    ]
    res = logged_client.delete(f"/transactions/{other_users_transactions[0].id}")
    assert res.status_code == 403
    assert res.json().get("detail") == "Not allowed"


def test_update_transaction_category_only(
    logged_client, test_transactions, test_categories
):
    updated_trans = {"category_id": test_categories[1].id}
    res = logged_client.put(
        f"/transactions/{test_transactions[0].id}", json=updated_trans
    )
    assert res.status_code == 200
    new_trans = schemas.Transaction(**res.json())
    assert new_trans.id == test_transactions[0].id
    assert new_trans.title == test_transactions[0].title
    assert new_trans.amount == test_transactions[0].amount
    assert new_trans.category_id == updated_trans["category_id"]
    assert new_trans.account_id == test_transactions[0].account_id


def test_transaction_includes_category_info(logged_client, test_transactions):
    res = logged_client.get(f"/transactions/{test_transactions[0].id}")
    assert res.status_code == 200
    transaction_data = res.json()
    assert "category" in transaction_data
    assert "id" in transaction_data["category"]
    assert "name" in transaction_data["category"]


def test_transaction_includes_account_info(logged_client, test_transactions):
    res = logged_client.get(f"/transactions/{test_transactions[0].id}")
    assert res.status_code == 200
    transaction_data = res.json()
    assert "account" in transaction_data
    assert "id" in transaction_data["account"]
    assert "name" in transaction_data["account"]
    assert "balance" in transaction_data["account"]

from app import models, schemas
from datetime import datetime, timezone, timedelta
from urllib.parse import quote


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
    response_data = res.json()

    # Check response structure
    assert "items" in response_data
    assert "pagination" in response_data

    user_transactions = [
        trans for trans in test_transactions if trans.user_id == test_user["id"]
    ]
    assert len(response_data["items"]) == len(user_transactions)

    # Validate transaction schema
    res_data = [schemas.Transaction(**trans) for trans in response_data["items"]]

    # Validate pagination info
    pagination = response_data["pagination"]
    assert pagination["total"] == len(user_transactions)
    assert pagination["limit"] == 50  # default limit
    assert pagination["offset"] == 0  # default offset


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
    db_session.expire_all()
    trans_query = db_session.query(models.Transaction).filter(
        models.Transaction.id == test_transactions[0].id
    )
    deleted_trans = trans_query.first()
    assert deleted_trans is not None
    assert deleted_trans.is_deleted == True


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


def test_get_all_transactions_pagination(test_user, logged_client, test_transactions):
    """Test pagination with limit and offset"""
    # Test with small limit
    res = logged_client.get("/transactions/?limit=2&offset=0")
    assert res.status_code == 200
    response_data = res.json()

    assert len(response_data["items"]) <= 2
    assert response_data["pagination"]["limit"] == 2
    assert response_data["pagination"]["offset"] == 0

    # Test offset
    res = logged_client.get("/transactions/?limit=2&offset=1")
    assert res.status_code == 200
    response_data = res.json()
    assert response_data["pagination"]["offset"] == 1


def test_get_all_transactions_sorting(test_user, logged_client, test_transactions):
    """Test sorting functionality"""
    # Test sort by amount ascending
    res = logged_client.get("/transactions/?sort_by=amount&sort_order=asc")
    assert res.status_code == 200
    response_data = res.json()
    items = response_data["items"]

    if len(items) > 1:
        # Check that amounts are in ascending order
        amounts = [item["amount"] for item in items]
        assert amounts == sorted(amounts)

    # Test sort by amount descending
    res = logged_client.get("/transactions/?sort_by=amount&sort_order=desc")
    assert res.status_code == 200
    response_data = res.json()
    items = response_data["items"]

    if len(items) > 1:
        # Check that amounts are in descending order
        amounts = [item["amount"] for item in items]
        assert amounts == sorted(amounts, reverse=True)


def test_get_all_transactions_search(test_user, logged_client, test_transactions):
    """Test search functionality"""
    # Search for a specific term that should match some transactions
    res = logged_client.get("/transactions/filter?search=Salary")
    assert res.status_code == 200
    transaction_ids = res.json()

    # Should return some transaction IDs
    assert isinstance(transaction_ids, list)
    assert len(transaction_ids) > 0

    # Verify that the returned transactions contain the search term
    for trans_id in transaction_ids:
        trans_res = logged_client.get(f"/transactions/{trans_id}")
        assert trans_res.status_code == 200
        transaction = trans_res.json()
        assert "Salary" in transaction["title"]


def test_get_all_transactions_category_filter(
    test_user, logged_client, test_transactions, test_categories
):
    """Test category filtering"""
    category_id = test_categories[0].id
    res = logged_client.get(f"/transactions/filter?category_id={category_id}")
    assert res.status_code == 200
    transaction_ids = res.json()

    # Should return some transaction IDs
    assert isinstance(transaction_ids, list)

    # Verify that all returned transactions have the specified category
    for trans_id in transaction_ids:
        trans_res = logged_client.get(f"/transactions/{trans_id}")
        assert trans_res.status_code == 200
        transaction = trans_res.json()
        assert transaction["category_id"] == category_id


def test_get_all_transactions_account_filter(
    test_user, logged_client, test_transactions, test_accounts
):
    """Test account filtering"""
    # Get the user's first account
    user_accounts = [acc for acc in test_accounts if acc.user_id == test_user["id"]]
    if user_accounts:
        account_id = user_accounts[0].id
        res = logged_client.get(f"/transactions/filter?account_id={account_id}")
        assert res.status_code == 200
        transaction_ids = res.json()

        # Should return some transaction IDs
        assert isinstance(transaction_ids, list)

        # Verify that all returned transactions have the specified account
        for trans_id in transaction_ids:
            trans_res = logged_client.get(f"/transactions/{trans_id}")
            assert trans_res.status_code == 200
            transaction = trans_res.json()
            assert transaction["account_id"] == account_id


def test_get_all_transactions_amount_filter(
    test_user, logged_client, test_transactions
):
    """Test amount range filtering"""
    # Test minimum amount filter
    res = logged_client.get("/transactions/filter?min_amount=100")
    assert res.status_code == 200
    transaction_ids = res.json()
    assert isinstance(transaction_ids, list)

    # Verify that all returned transactions have amount >= 100
    for trans_id in transaction_ids:
        trans_res = logged_client.get(f"/transactions/{trans_id}")
        assert trans_res.status_code == 200
        transaction = trans_res.json()
        assert transaction["amount"] >= 100

    # Test maximum amount filter
    res = logged_client.get("/transactions/filter?max_amount=1000")
    assert res.status_code == 200
    transaction_ids = res.json()
    assert isinstance(transaction_ids, list)

    # Verify that all returned transactions have amount <= 1000
    for trans_id in transaction_ids:
        trans_res = logged_client.get(f"/transactions/{trans_id}")
        assert trans_res.status_code == 200
        transaction = trans_res.json()
        assert transaction["amount"] <= 1000

    # Test range filter
    res = logged_client.get("/transactions/filter?min_amount=100&max_amount=1000")
    assert res.status_code == 200
    transaction_ids = res.json()
    assert isinstance(transaction_ids, list)

    # Verify that all returned transactions are within range
    for trans_id in transaction_ids:
        trans_res = logged_client.get(f"/transactions/{trans_id}")
        assert trans_res.status_code == 200
        transaction = trans_res.json()
        assert 100 <= transaction["amount"] <= 1000


def test_get_all_transactions_date_filter(test_user, logged_client, test_transactions):
    """Test date range filtering"""
    from datetime import datetime, timedelta

    # Test future date filter (should return no results for past transactions)
    future_date = (datetime.now() + timedelta(days=1)).isoformat()
    res = logged_client.get(f"/transactions/filter?from_date={future_date}")
    assert res.status_code == 200
    transaction_ids = res.json()
    # Should return no transactions since all test transactions are in the past/present
    assert transaction_ids == []

    # Test past date filter
    past_date = (datetime.now() - timedelta(days=30)).isoformat()
    res = logged_client.get(f"/transactions/filter?from_date={past_date}")
    assert res.status_code == 200
    transaction_ids = res.json()
    # This should work without errors and return some transactions
    assert isinstance(transaction_ids, list)


def test_get_all_transactions_invalid_sort_field(logged_client):
    """Test invalid sort field validation"""
    res = logged_client.get("/transactions/?sort_by=invalid_field")
    assert res.status_code == 422  # Validation error


def test_get_all_transactions_invalid_sort_order(logged_client):
    """Test invalid sort order validation"""
    res = logged_client.get("/transactions/?sort_order=invalid_order")
    assert res.status_code == 422  # Validation error


def test_get_all_transactions_forbidden_category(
    test_users, logged_client, test_categories
):
    """Test access to forbidden category"""
    # Try to filter by a category that doesn't belong to the user
    other_user_categories = [
        cat for cat in test_categories if cat.user_id != test_users[0]["id"]
    ]
    if other_user_categories:
        category_id = other_user_categories[0].id
        res = logged_client.get(f"/transactions/filter?category_id={category_id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"


def test_get_all_transactions_forbidden_account(
    test_users, logged_client, test_accounts
):
    """Test access to forbidden account"""
    # Try to filter by an account that doesn't belong to the user
    other_user_accounts = [
        acc for acc in test_accounts if acc.user_id != test_users[0]["id"]
    ]
    if other_user_accounts:
        account_id = other_user_accounts[0].id
        res = logged_client.get(f"/transactions/filter?account_id={account_id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"


def test_get_updated_transactions_since(
    logged_client,
    test_transactions,
    db_session,
    test_user,
):

    # Set all test transactions to have old updated_at timestamps
    old_time = datetime.now(timezone.utc) - timedelta(hours=1)
    for trans in test_transactions:
        db_session.query(models.Transaction).filter(
            models.Transaction.id == trans.id
        ).update({"updated_at": old_time}, synchronize_session=False)
    db_session.commit()

    # Set baseline to now (after the old timestamps)
    baseline = datetime.now(timezone.utc)
    baseline_param = int(baseline.timestamp())

    res = logged_client.get(f"/transactions/updated?updated_since={baseline_param}")
    assert res.status_code == 200, res.json()
    assert res.json() == []

    update_payload = {"title": "Updated title"}
    res_update = logged_client.put(
        f"/transactions/{test_transactions[0].id}", json=update_payload
    )
    assert res_update.status_code == 200

    other_transaction = next(
        trans for trans in test_transactions if trans.user_id != test_user["id"]
    )
    db_session.query(models.Transaction).filter(
        models.Transaction.id == other_transaction.id
    ).update({"updated_at": baseline + timedelta(minutes=5)}, synchronize_session=False)
    db_session.commit()

    res = logged_client.get(f"/transactions/updated?updated_since={baseline_param}")
    assert res.status_code == 200, res.json()
    payload = res.json()
    assert test_transactions[0].id in payload
    assert other_transaction.id not in payload

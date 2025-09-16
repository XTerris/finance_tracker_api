from app import schemas
from app import models
import pytest


class TestCreateAccount:
    def test_create_account(self, logged_client):
        account_data = {"name": "Business Account", "balance": 2500.0}
        res = logged_client.post("/accounts/", json=account_data)
        assert res.status_code == 201
        new_account = schemas.Account(**res.json())
        assert new_account.name == account_data["name"]
        assert new_account.balance == account_data["balance"]
        assert new_account.user_id is not None

    def test_create_account_zero_balance(self, logged_client):
        account_data = {"name": "Zero Account", "balance": 0.0}
        res = logged_client.post("/accounts/", json=account_data)
        assert res.status_code == 201
        new_account = schemas.Account(**res.json())
        assert new_account.balance == 0.0

    def test_create_account_negative_balance(self, logged_client):
        account_data = {"name": "Credit Account", "balance": -1000.0}
        res = logged_client.post("/accounts/", json=account_data)
        assert res.status_code == 201
        new_account = schemas.Account(**res.json())
        assert new_account.balance == -1000.0

    def test_create_account_unauthorized(self, client):
        account_data = {"name": "Unauthorized Account", "balance": 1000.0}
        res = client.post("/accounts/", json=account_data)
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_create_account_missing_name(self, logged_client):
        account_data = {"balance": 1000.0}
        res = logged_client.post("/accounts/", json=account_data)
        assert res.status_code == 422

    def test_create_account_missing_balance(self, logged_client):
        account_data = {"name": "No Balance Account"}
        res = logged_client.post("/accounts/", json=account_data)
        assert res.status_code == 422

    def test_create_account_invalid_balance_type(self, logged_client):
        account_data = {"name": "Invalid Balance", "balance": "not_a_number"}
        res = logged_client.post("/accounts/", json=account_data)
        assert res.status_code == 422


class TestGetAccount:
    def test_get_account_by_id(self, logged_client, test_accounts):
        # Get user's own account
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:  # test_user's id
                user_account = acc
                break

        assert user_account is not None
        res = logged_client.get(f"/accounts/{user_account.id}")
        assert res.status_code == 200
        account = schemas.Account(**res.json())
        assert account.id == user_account.id
        assert account.name == user_account.name
        assert account.balance == user_account.balance

    def test_get_account_unauthorized(self, client, test_accounts):
        res = client.get(f"/accounts/{test_accounts[0].id}")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_get_account_forbidden(self, logged_client, test_accounts):
        # Try to access another user's account
        other_user_account = None
        for acc in test_accounts:
            if acc.user_id == 2:  # Different user's account
                other_user_account = acc
                break

        assert other_user_account is not None
        res = logged_client.get(f"/accounts/{other_user_account.id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_get_account_not_found(self, logged_client):
        res = logged_client.get("/accounts/999999")
        assert res.status_code == 404
        assert res.json().get("detail") == "Account was not found"


class TestGetAllAccounts:
    def test_get_all_accounts(self, logged_client, test_accounts):
        res = logged_client.get("/accounts/")
        assert res.status_code == 200
        accounts = res.json()

        # Should return only user's accounts
        user_accounts = []
        for acc in test_accounts:
            if acc.user_id == 1:  # User's accounts only
                user_accounts.append(acc)

        assert len(accounts) == len(user_accounts)
        for account in accounts:
            account_obj = schemas.Account(**account)
            assert account_obj.user_id == 1

    def test_get_all_accounts_with_search(self, logged_client, test_accounts):
        # Search for accounts containing "Checking"
        res = logged_client.get("/accounts/?search=Checking")
        assert res.status_code == 200
        accounts = res.json()

        for account in accounts:
            assert "Checking" in account["name"]

    def test_get_all_accounts_with_limit(self, logged_client, test_accounts):
        res = logged_client.get("/accounts/?limit=1")
        assert res.status_code == 200
        accounts = res.json()
        assert len(accounts) <= 1

    def test_get_all_accounts_unauthorized(self, client):
        res = client.get("/accounts/")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_get_all_accounts_empty_result(self, logged_client):
        # Search for something that doesn't exist
        res = logged_client.get("/accounts/?search=NonExistentAccount")
        assert res.status_code == 200
        accounts = res.json()
        assert len(accounts) == 0


class TestUpdateAccount:
    def test_update_account_name(self, logged_client, test_accounts):
        # Get user's own account
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:  # test_user's id
                user_account = acc
                break

        assert user_account is not None
        update_data = {"name": "Updated Account Name"}
        res = logged_client.put(f"/accounts/{user_account.id}", json=update_data)
        assert res.status_code == 200
        updated_account = schemas.Account(**res.json())
        assert updated_account.name == update_data["name"]
        assert updated_account.id == user_account.id
        assert (
            updated_account.balance == user_account.balance
        )  # Balance should remain unchanged

    def test_update_account_balance(self, logged_client, test_accounts):
        # Get user's own account
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        assert user_account is not None
        update_data = {"balance": 3000.0}
        res = logged_client.put(f"/accounts/{user_account.id}", json=update_data)
        assert res.status_code == 200
        updated_account = schemas.Account(**res.json())
        assert updated_account.balance == update_data["balance"]
        assert updated_account.name == user_account.name  # Name should remain unchanged

    def test_update_account_both_fields(self, logged_client, test_accounts):
        # Get user's own account
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        assert user_account is not None
        update_data = {"name": "Completely New Account", "balance": 7500.0}
        res = logged_client.put(f"/accounts/{user_account.id}", json=update_data)
        assert res.status_code == 200
        updated_account = schemas.Account(**res.json())
        assert updated_account.name == update_data["name"]
        assert updated_account.balance == update_data["balance"]

    def test_update_account_partial(self, logged_client, test_accounts):
        # Test partial update with valid data
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        assert user_account is not None
        original_name = user_account.name
        original_balance = user_account.balance
        update_data = {"name": "Partially Updated Name"}
        res = logged_client.put(f"/accounts/{user_account.id}", json=update_data)
        assert res.status_code == 200
        updated_account = schemas.Account(**res.json())
        assert updated_account.name == update_data["name"]
        assert updated_account.name != original_name
        assert updated_account.balance == original_balance  # Balance unchanged

    def test_update_account_unauthorized(self, client, test_accounts):
        update_data = {"name": "Unauthorized Update"}
        res = client.put(f"/accounts/{test_accounts[0].id}", json=update_data)
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_update_account_forbidden(self, logged_client, test_accounts):
        # Try to update another user's account
        other_user_account = None
        for acc in test_accounts:
            if acc.user_id == 2:  # Different user's account
                other_user_account = acc
                break

        assert other_user_account is not None
        update_data = {"name": "Hacked Account"}
        res = logged_client.put(f"/accounts/{other_user_account.id}", json=update_data)
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_update_account_not_found(self, logged_client):
        update_data = {"name": "Non-existent Account"}
        res = logged_client.put("/accounts/999999", json=update_data)
        assert res.status_code == 404
        assert res.json().get("detail") == "Account was not found"

    def test_update_account_invalid_balance_type(self, logged_client, test_accounts):
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        assert user_account is not None
        update_data = {"balance": "invalid_balance"}
        res = logged_client.put(f"/accounts/{user_account.id}", json=update_data)
        assert res.status_code == 422


class TestDeleteAccount:
    def test_delete_account(self, logged_client, test_users, db_session):
        # Create a new account to delete
        new_account = models.Account(
            name="Deletable Account", balance=500.0, user_id=test_users[0]["id"]
        )
        db_session.add(new_account)
        db_session.commit()
        db_session.refresh(new_account)

        res = logged_client.delete(f"/accounts/{new_account.id}")
        assert res.status_code == 204

    def test_delete_account_unauthorized(self, client, test_accounts):
        res = client.delete(f"/accounts/{test_accounts[0].id}")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_delete_account_forbidden(self, logged_client, test_accounts):
        # Try to delete another user's account
        other_user_account = None
        for acc in test_accounts:
            if acc.user_id == 2:  # Different user's account
                other_user_account = acc
                break

        assert other_user_account is not None
        res = logged_client.delete(f"/accounts/{other_user_account.id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_delete_account_not_found(self, logged_client):
        res = logged_client.delete("/accounts/999999")
        assert res.status_code == 404
        assert res.json().get("detail") == "Account was not found"

from app import schemas
from app import models
import pytest


class TestCreateCategory:
    def test_create_category(self, logged_client):
        category_data = {"name": "Food"}
        res = logged_client.post("/categories/", json=category_data)
        assert res.status_code == 201
        new_category = schemas.Category(**res.json())
        assert new_category.name == category_data["name"]
        assert new_category.user_id is not None

    def test_create_category_unauthorized(self, client):
        category_data = {"name": "Food"}
        res = client.post("/categories/", json=category_data)
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_create_category_missing_name(self, logged_client):
        category_data = {}
        res = logged_client.post("/categories/", json=category_data)
        assert res.status_code == 422


class TestGetCategory:
    def test_get_category_by_id(self, logged_client, test_categories):
        # Get user's own category
        user_category = None
        for cat in test_categories:
            if cat.user_id == 1:  # test_user's id
                user_category = cat
                break

        assert user_category is not None
        res = logged_client.get(f"/categories/{user_category.id}")
        assert res.status_code == 200
        category = schemas.Category(**res.json())
        assert category.id == user_category.id
        assert category.name == user_category.name

    def test_get_system_category(self, logged_client, test_categories):
        # Get system category (user_id is None)
        system_category = None
        for cat in test_categories:
            if cat.user_id is None:
                system_category = cat
                break

        assert system_category is not None
        res = logged_client.get(f"/categories/{system_category.id}")
        assert res.status_code == 200
        category = schemas.Category(**res.json())
        assert category.id == system_category.id
        assert category.user_id is None

    def test_get_category_unauthorized(self, client, test_categories):
        res = client.get(f"/categories/{test_categories[0].id}")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_get_category_forbidden(self, logged_client, test_categories):
        # Try to access another user's category
        other_user_category = None
        for cat in test_categories:
            if cat.user_id == 2:  # Different user's category
                other_user_category = cat
                break

        assert other_user_category is not None
        res = logged_client.get(f"/categories/{other_user_category.id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_get_category_not_found(self, logged_client):
        res = logged_client.get("/categories/999999")
        assert res.status_code == 404
        assert res.json().get("detail") == "Category was not found"


class TestGetAllCategories:
    def test_get_all_categories(self, logged_client, test_categories):
        res = logged_client.get("/categories/")
        assert res.status_code == 200
        categories = res.json()

        # Should return user's categories + system categories
        user_and_system_categories = []
        for cat in test_categories:
            if (
                cat.user_id == 1 or cat.user_id is None
            ):  # User's categories or system categories
                user_and_system_categories.append(cat)

        assert len(categories) == len(user_and_system_categories)

    def test_get_all_categories_with_search(self, logged_client, test_categories):
        # Search for categories containing "Income"
        res = logged_client.get("/categories/?search=Income")
        assert res.status_code == 200
        categories = res.json()

        for category in categories:
            assert "Income" in category["name"]

    def test_get_all_categories_with_limit(self, logged_client, test_categories):
        res = logged_client.get("/categories/?limit=1")
        assert res.status_code == 200
        categories = res.json()
        assert len(categories) <= 1

    def test_get_all_categories_unauthorized(self, client):
        res = client.get("/categories/")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"


class TestUpdateCategory:
    def test_update_category(self, logged_client, test_categories):
        # Get user's own category
        user_category = None
        for cat in test_categories:
            if cat.user_id == 1:  # test_user's id
                user_category = cat
                break

        assert user_category is not None
        update_data = {"name": "Updated Category Name"}
        res = logged_client.put(f"/categories/{user_category.id}", json=update_data)
        assert res.status_code == 200
        updated_category = schemas.Category(**res.json())
        assert updated_category.name == update_data["name"]
        assert updated_category.id == user_category.id

    def test_update_category_partial(self, logged_client, test_categories):
        # Test partial update with a valid name
        user_category = None
        for cat in test_categories:
            if cat.user_id == 1:
                user_category = cat
                break

        assert user_category is not None
        original_name = user_category.name
        update_data = {"name": "Partially Updated Name"}
        res = logged_client.put(f"/categories/{user_category.id}", json=update_data)
        assert res.status_code == 200
        updated_category = schemas.Category(**res.json())
        assert updated_category.name == update_data["name"]
        assert updated_category.name != original_name

    def test_update_category_unauthorized(self, client, test_categories):
        update_data = {"name": "Updated Name"}
        res = client.put(f"/categories/{test_categories[0].id}", json=update_data)
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_update_category_forbidden_other_user(self, logged_client, test_categories):
        # Try to update another user's category
        other_user_category = None
        for cat in test_categories:
            if cat.user_id == 2:  # Different user's category
                other_user_category = cat
                break

        assert other_user_category is not None
        update_data = {"name": "Hacked Name"}
        res = logged_client.put(
            f"/categories/{other_user_category.id}", json=update_data
        )
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_update_category_forbidden_system_category(
        self, logged_client, test_categories
    ):
        # Try to update system category
        system_category = None
        for cat in test_categories:
            if cat.user_id is None:
                system_category = cat
                break

        assert system_category is not None
        update_data = {"name": "Hacked System Category"}
        res = logged_client.put(f"/categories/{system_category.id}", json=update_data)
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_update_category_not_found(self, logged_client):
        update_data = {"name": "Updated Name"}
        res = logged_client.put("/categories/999999", json=update_data)
        assert res.status_code == 404
        assert res.json().get("detail") == "Category was not found"


class TestDeleteCategory:
    def test_delete_category(self, logged_client, test_users, db_session):
        # Create a category that's not being used by transactions
        new_category = models.Category(
            name="Deletable Category", user_id=test_users[0]["id"]
        )
        db_session.add(new_category)
        db_session.commit()
        db_session.refresh(new_category)

        res = logged_client.delete(f"/categories/{new_category.id}")
        assert res.status_code == 204

    def test_delete_category_unauthorized(self, client, test_categories):
        res = client.delete(f"/categories/{test_categories[0].id}")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_delete_category_forbidden_other_user(self, logged_client, test_categories):
        # Try to delete another user's category
        other_user_category = None
        for cat in test_categories:
            if cat.user_id == 2:  # Different user's category
                other_user_category = cat
                break

        assert other_user_category is not None
        res = logged_client.delete(f"/categories/{other_user_category.id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_delete_category_forbidden_system_category(
        self, logged_client, test_categories
    ):
        # Try to delete system category
        system_category = None
        for cat in test_categories:
            if cat.user_id is None:
                system_category = cat
                break

        assert system_category is not None
        res = logged_client.delete(f"/categories/{system_category.id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_delete_category_not_found(self, logged_client):
        res = logged_client.delete("/categories/999999")
        assert res.status_code == 404
        assert res.json().get("detail") == "Category was not found"

    def test_delete_category_with_transactions(
        self, logged_client, test_categories, test_transactions
    ):
        # Try to delete a category that has transactions
        # Find a category that's being used
        category_with_transactions = None
        for cat in test_categories:
            if cat.user_id == 1:  # User's category
                for trans in test_transactions:
                    if trans.category_id == cat.id:
                        category_with_transactions = cat
                        break
                if category_with_transactions:
                    break

        assert category_with_transactions is not None
        res = logged_client.delete(f"/categories/{category_with_transactions.id}")
        assert res.status_code == 400
        assert (
            res.json().get("detail")
            == "Cannot delete category that is being used by transactions"
        )

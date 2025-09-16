from app import schemas
from app import models
import pytest
from datetime import date, timedelta


class TestCreateGoal:
    def test_create_goal(self, logged_client, test_accounts):
        # Get user's account
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:  # test_user's id
                user_account = acc
                break

        assert user_account is not None
        goal_data = {
            "account_id": user_account.id,
            "target_amount": 15000.0,
            "deadline": str(date.today() + timedelta(days=180))
        }
        res = logged_client.post("/goals/", json=goal_data)
        assert res.status_code == 201
        new_goal = schemas.Goal(**res.json())
        assert new_goal.account_id == goal_data["account_id"]
        assert new_goal.target_amount == goal_data["target_amount"]
        assert str(new_goal.deadline) == goal_data["deadline"]
        assert new_goal.user_id == 1
        assert new_goal.is_completed == False

    def test_create_goal_with_past_deadline(self, logged_client, test_accounts):
        # Test creating goal with past deadline (should still work)
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        assert user_account is not None
        goal_data = {
            "account_id": user_account.id,
            "target_amount": 5000.0,
            "deadline": str(date.today() - timedelta(days=30))  # Past date
        }
        res = logged_client.post("/goals/", json=goal_data)
        assert res.status_code == 201
        new_goal = schemas.Goal(**res.json())
        assert new_goal.target_amount == goal_data["target_amount"]

    def test_create_goal_unauthorized(self, client, test_accounts):
        goal_data = {
            "account_id": test_accounts[0].id,
            "target_amount": 10000.0,
            "deadline": str(date.today() + timedelta(days=365))
        }
        res = client.post("/goals/", json=goal_data)
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_create_goal_forbidden_account(self, logged_client, test_accounts):
        # Try to create goal for another user's account
        other_user_account = None
        for acc in test_accounts:
            if acc.user_id == 2:  # Different user's account
                other_user_account = acc
                break

        assert other_user_account is not None
        goal_data = {
            "account_id": other_user_account.id,
            "target_amount": 10000.0,
            "deadline": str(date.today() + timedelta(days=365))
        }
        res = logged_client.post("/goals/", json=goal_data)
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_create_goal_nonexistent_account(self, logged_client):
        goal_data = {
            "account_id": 999999,
            "target_amount": 10000.0,
            "deadline": str(date.today() + timedelta(days=365))
        }
        res = logged_client.post("/goals/", json=goal_data)
        assert res.status_code == 404
        assert res.json().get("detail") == "Account was not found"

    def test_create_goal_missing_fields(self, logged_client, test_accounts):
        # Missing target_amount
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        goal_data = {
            "account_id": user_account.id,
            "deadline": str(date.today() + timedelta(days=365))
        }
        res = logged_client.post("/goals/", json=goal_data)
        assert res.status_code == 422

    def test_create_goal_invalid_amount(self, logged_client, test_accounts):
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        goal_data = {
            "account_id": user_account.id,
            "target_amount": "not_a_number",
            "deadline": str(date.today() + timedelta(days=365))
        }
        res = logged_client.post("/goals/", json=goal_data)
        assert res.status_code == 422

    def test_create_goal_invalid_date(self, logged_client, test_accounts):
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        goal_data = {
            "account_id": user_account.id,
            "target_amount": 10000.0,
            "deadline": "not_a_date"
        }
        res = logged_client.post("/goals/", json=goal_data)
        assert res.status_code == 422


class TestGetGoal:
    def test_get_goal_by_id(self, logged_client, test_goals):
        # Get user's own goal
        user_goal = None
        for goal in test_goals:
            if goal.user_id == 1:  # test_user's id
                user_goal = goal
                break

        assert user_goal is not None
        res = logged_client.get(f"/goals/{user_goal.id}")
        assert res.status_code == 200
        goal = schemas.Goal(**res.json())
        assert goal.id == user_goal.id
        assert goal.target_amount == user_goal.target_amount
        assert goal.is_completed == user_goal.is_completed
        assert goal.user_id == user_goal.user_id

    def test_get_goal_unauthorized(self, client, test_goals):
        res = client.get(f"/goals/{test_goals[0].id}")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_get_goal_forbidden(self, logged_client, test_goals):
        # Try to access another user's goal
        other_user_goal = None
        for goal in test_goals:
            if goal.user_id == 2:  # Different user's goal
                other_user_goal = goal
                break

        assert other_user_goal is not None
        res = logged_client.get(f"/goals/{other_user_goal.id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_get_goal_not_found(self, logged_client):
        res = logged_client.get("/goals/999999")
        assert res.status_code == 404
        assert res.json().get("detail") == "Goal was not found"


class TestGetAllGoals:
    def test_get_all_goals(self, logged_client, test_goals):
        res = logged_client.get("/goals/")
        assert res.status_code == 200
        goals = res.json()

        # Should return only user's goals
        user_goals = []
        for goal in test_goals:
            if goal.user_id == 1:  # User's goals only
                user_goals.append(goal)

        assert len(goals) == len(user_goals)
        for goal in goals:
            goal_obj = schemas.Goal(**goal)
            assert goal_obj.user_id == 1

    def test_get_all_goals_with_completed_filter(self, logged_client, test_goals):
        # Filter for completed goals only
        res = logged_client.get("/goals/?completed=true")
        assert res.status_code == 200
        goals = res.json()

        for goal in goals:
            assert goal["is_completed"] == True
            assert goal["user_id"] == 1

    def test_get_all_goals_with_incomplete_filter(self, logged_client, test_goals):
        # Filter for incomplete goals only
        res = logged_client.get("/goals/?completed=false")
        assert res.status_code == 200
        goals = res.json()

        for goal in goals:
            assert goal["is_completed"] == False
            assert goal["user_id"] == 1

    def test_get_all_goals_with_limit(self, logged_client, test_goals):
        res = logged_client.get("/goals/?limit=1")
        assert res.status_code == 200
        goals = res.json()
        assert len(goals) <= 1

    def test_get_all_goals_unauthorized(self, client):
        res = client.get("/goals/")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_get_all_goals_empty_result(self, logged_client, test_users, db_session):
        # Create a user with no goals
        from app.oauth2 import create_access_token
        from fastapi.testclient import TestClient
        
        # Create third user
        user_data = {
            "username": "no_goals_user",
            "login": "no_goals_login",
            "password": "test_password",
        }
        user_res = logged_client.post("/users/", json=user_data)
        assert user_res.status_code == 201
        new_user = user_res.json()
        
        # Create token for this user
        token = create_access_token(data={"user_id": new_user["id"]})
        headers = {"Authorization": f"Bearer {token}"}
        
        res = logged_client.get("/goals/", headers=headers)
        assert res.status_code == 200
        goals = res.json()
        assert len(goals) == 0


class TestUpdateGoal:
    def test_update_goal_target_amount(self, logged_client, test_goals):
        # Get user's own goal
        user_goal = None
        for goal in test_goals:
            if goal.user_id == 1:  # test_user's id
                user_goal = goal
                break

        assert user_goal is not None
        update_data = {"target_amount": 25000.0}
        res = logged_client.put(f"/goals/{user_goal.id}", json=update_data)
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert updated_goal.target_amount == update_data["target_amount"]
        assert updated_goal.id == user_goal.id
        assert updated_goal.deadline == user_goal.deadline  # Should remain unchanged

    def test_update_goal_deadline(self, logged_client, test_goals):
        user_goal = None
        for goal in test_goals:
            if goal.user_id == 1:
                user_goal = goal
                break

        assert user_goal is not None
        new_deadline = str(date.today() + timedelta(days=500))
        update_data = {"deadline": new_deadline}
        res = logged_client.put(f"/goals/{user_goal.id}", json=update_data)
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert str(updated_goal.deadline) == new_deadline
        assert updated_goal.target_amount == user_goal.target_amount  # Should remain unchanged

    def test_update_goal_completion_status(self, logged_client, test_goals):
        user_goal = None
        for goal in test_goals:
            if goal.user_id == 1 and not goal.is_completed:
                user_goal = goal
                break

        assert user_goal is not None
        update_data = {"is_completed": True}
        res = logged_client.put(f"/goals/{user_goal.id}", json=update_data)
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert updated_goal.is_completed == True

    def test_update_goal_account_id(self, logged_client, test_goals, test_accounts):
        user_goal = None
        for goal in test_goals:
            if goal.user_id == 1:
                user_goal = goal
                break

        # Find a different account belonging to the same user
        other_account = None
        for acc in test_accounts:
            if acc.user_id == 1 and acc.id != user_goal.account_id:
                other_account = acc
                break

        assert user_goal is not None
        assert other_account is not None
        update_data = {"account_id": other_account.id}
        res = logged_client.put(f"/goals/{user_goal.id}", json=update_data)
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert updated_goal.account_id == other_account.id

    def test_update_goal_multiple_fields(self, logged_client, test_goals):
        user_goal = None
        for goal in test_goals:
            if goal.user_id == 1:
                user_goal = goal
                break

        assert user_goal is not None
        update_data = {
            "target_amount": 30000.0,
            "deadline": str(date.today() + timedelta(days=600)),
            "is_completed": True
        }
        res = logged_client.put(f"/goals/{user_goal.id}", json=update_data)
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert updated_goal.target_amount == update_data["target_amount"]
        assert str(updated_goal.deadline) == update_data["deadline"]
        assert updated_goal.is_completed == update_data["is_completed"]

    def test_update_goal_unauthorized(self, client, test_goals):
        update_data = {"target_amount": 20000.0}
        res = client.put(f"/goals/{test_goals[0].id}", json=update_data)
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_update_goal_forbidden(self, logged_client, test_goals):
        # Try to update another user's goal
        other_user_goal = None
        for goal in test_goals:
            if goal.user_id == 2:  # Different user's goal
                other_user_goal = goal
                break

        assert other_user_goal is not None
        update_data = {"target_amount": 999999.0}
        res = logged_client.put(f"/goals/{other_user_goal.id}", json=update_data)
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_update_goal_not_found(self, logged_client):
        update_data = {"target_amount": 20000.0}
        res = logged_client.put("/goals/999999", json=update_data)
        assert res.status_code == 404
        assert res.json().get("detail") == "Goal was not found"

    def test_update_goal_forbidden_account(self, logged_client, test_goals, test_accounts):
        # Try to update goal to use another user's account
        user_goal = None
        for goal in test_goals:
            if goal.user_id == 1:
                user_goal = goal
                break

        other_user_account = None
        for acc in test_accounts:
            if acc.user_id == 2:  # Different user's account
                other_user_account = acc
                break

        assert user_goal is not None
        assert other_user_account is not None
        update_data = {"account_id": other_user_account.id}
        res = logged_client.put(f"/goals/{user_goal.id}", json=update_data)
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_update_goal_nonexistent_account(self, logged_client, test_goals):
        user_goal = None
        for goal in test_goals:
            if goal.user_id == 1:
                user_goal = goal
                break

        assert user_goal is not None
        update_data = {"account_id": 999999}
        res = logged_client.put(f"/goals/{user_goal.id}", json=update_data)
        assert res.status_code == 404
        assert res.json().get("detail") == "Account was not found"


class TestDeleteGoal:
    def test_delete_goal(self, logged_client, test_users, test_accounts, db_session):
        # Create a new goal to delete
        user_account = None
        for acc in test_accounts:
            if acc.user_id == 1:
                user_account = acc
                break

        assert user_account is not None
        new_goal = models.Goal(
            user_id=test_users[0]["id"],
            account_id=user_account.id,
            target_amount=5000.0,
            deadline=date.today() + timedelta(days=100),
            is_completed=False
        )
        db_session.add(new_goal)
        db_session.commit()
        db_session.refresh(new_goal)

        res = logged_client.delete(f"/goals/{new_goal.id}")
        assert res.status_code == 204

    def test_delete_goal_unauthorized(self, client, test_goals):
        res = client.delete(f"/goals/{test_goals[0].id}")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_delete_goal_forbidden(self, logged_client, test_goals):
        # Try to delete another user's goal
        other_user_goal = None
        for goal in test_goals:
            if goal.user_id == 2:  # Different user's goal
                other_user_goal = goal
                break

        assert other_user_goal is not None
        res = logged_client.delete(f"/goals/{other_user_goal.id}")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_delete_goal_not_found(self, logged_client):
        res = logged_client.delete("/goals/999999")
        assert res.status_code == 404
        assert res.json().get("detail") == "Goal was not found"


class TestMarkGoalComplete:
    def test_mark_goal_complete(self, logged_client, test_goals):
        # Find an incomplete goal
        incomplete_goal = None
        for goal in test_goals:
            if goal.user_id == 1 and not goal.is_completed:
                incomplete_goal = goal
                break

        assert incomplete_goal is not None
        res = logged_client.patch(f"/goals/{incomplete_goal.id}/complete")
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert updated_goal.is_completed == True
        assert updated_goal.id == incomplete_goal.id

    def test_mark_goal_complete_already_completed(self, logged_client, test_goals):
        # Find a completed goal
        completed_goal = None
        for goal in test_goals:
            if goal.user_id == 1 and goal.is_completed:
                completed_goal = goal
                break

        assert completed_goal is not None
        res = logged_client.patch(f"/goals/{completed_goal.id}/complete")
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert updated_goal.is_completed == True  # Should remain true

    def test_mark_goal_complete_unauthorized(self, client, test_goals):
        res = client.patch(f"/goals/{test_goals[0].id}/complete")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_mark_goal_complete_forbidden(self, logged_client, test_goals):
        # Try to mark another user's goal as complete
        other_user_goal = None
        for goal in test_goals:
            if goal.user_id == 2:
                other_user_goal = goal
                break

        assert other_user_goal is not None
        res = logged_client.patch(f"/goals/{other_user_goal.id}/complete")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_mark_goal_complete_not_found(self, logged_client):
        res = logged_client.patch("/goals/999999/complete")
        assert res.status_code == 404
        assert res.json().get("detail") == "Goal was not found"


class TestMarkGoalIncomplete:
    def test_mark_goal_incomplete(self, logged_client, test_goals):
        # Find a completed goal
        completed_goal = None
        for goal in test_goals:
            if goal.user_id == 1 and goal.is_completed:
                completed_goal = goal
                break

        assert completed_goal is not None
        res = logged_client.patch(f"/goals/{completed_goal.id}/incomplete")
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert updated_goal.is_completed == False
        assert updated_goal.id == completed_goal.id

    def test_mark_goal_incomplete_already_incomplete(self, logged_client, test_goals):
        # Find an incomplete goal
        incomplete_goal = None
        for goal in test_goals:
            if goal.user_id == 1 and not goal.is_completed:
                incomplete_goal = goal
                break

        assert incomplete_goal is not None
        res = logged_client.patch(f"/goals/{incomplete_goal.id}/incomplete")
        assert res.status_code == 200
        updated_goal = schemas.Goal(**res.json())
        assert updated_goal.is_completed == False  # Should remain false

    def test_mark_goal_incomplete_unauthorized(self, client, test_goals):
        res = client.patch(f"/goals/{test_goals[0].id}/incomplete")
        assert res.status_code == 401
        assert res.json().get("detail") == "Not authenticated"

    def test_mark_goal_incomplete_forbidden(self, logged_client, test_goals):
        # Try to mark another user's goal as incomplete
        other_user_goal = None
        for goal in test_goals:
            if goal.user_id == 2:
                other_user_goal = goal
                break

        assert other_user_goal is not None
        res = logged_client.patch(f"/goals/{other_user_goal.id}/incomplete")
        assert res.status_code == 403
        assert res.json().get("detail") == "Not allowed"

    def test_mark_goal_incomplete_not_found(self, logged_client):
        res = logged_client.patch("/goals/999999/incomplete")
        assert res.status_code == 404
        assert res.json().get("detail") == "Goal was not found"
from app import schemas
from app import models
from app.oauth2 import create_access_token
import pytest
from datetime import date, timedelta


class TestCreateReminder:
    def test_create_reminder(self, logged_client):
        reminder_data = {
            "title": "Pay electricity bill",
            "amount": 150.50,
            "date": str(date.today() + timedelta(days=7)),
            "recurrence": None,
        }
        res = logged_client.post("/reminders/", json=reminder_data)
        assert res.status_code == 201
        new_reminder = schemas.Reminder(**res.json())
        assert new_reminder.title == reminder_data["title"]
        assert new_reminder.amount == reminder_data["amount"]
        assert str(new_reminder.date) == reminder_data["date"]
        assert new_reminder.recurrence is None
        assert new_reminder.user_id == 1
        assert new_reminder.is_active == True

    def test_create_recurring_reminder(self, logged_client):
        reminder_data = {
            "title": "Monthly rent payment",
            "amount": 1200.0,
            "date": str(date.today() + timedelta(days=30)),
            "recurrence": "P30D",  # ISO 8601 duration format for 30 days
        }
        res = logged_client.post("/reminders/", json=reminder_data)
        assert res.status_code == 201
        new_reminder = schemas.Reminder(**res.json())
        assert new_reminder.title == reminder_data["title"]
        assert new_reminder.amount == reminder_data["amount"]
        assert new_reminder.recurrence is not None

    def test_create_reminder_with_past_date(self, logged_client):
        # Test creating reminder with past date (should still work)
        reminder_data = {
            "title": "Late payment",
            "amount": 50.0,
            "date": str(date.today() - timedelta(days=5)),
            "recurrence": None,
        }
        res = logged_client.post("/reminders/", json=reminder_data)
        assert res.status_code == 201
        new_reminder = schemas.Reminder(**res.json())
        assert new_reminder.amount == reminder_data["amount"]

    def test_create_reminder_unauthorized(self, client):
        reminder_data = {
            "title": "Test reminder",
            "amount": 100.0,
            "date": str(date.today() + timedelta(days=7)),
            "recurrence": None,
        }
        res = client.post("/reminders/", json=reminder_data)
        assert res.status_code == 401

    def test_create_reminder_missing_fields(self, logged_client):
        # Test missing title
        reminder_data = {
            "amount": 100.0,
            "date": str(date.today() + timedelta(days=7)),
        }
        res = logged_client.post("/reminders/", json=reminder_data)
        assert res.status_code == 422

        # Test missing amount
        reminder_data = {
            "title": "Test reminder",
            "date": str(date.today() + timedelta(days=7)),
        }
        res = logged_client.post("/reminders/", json=reminder_data)
        assert res.status_code == 422

        # Test missing date
        reminder_data = {
            "title": "Test reminder",
            "amount": 100.0,
        }
        res = logged_client.post("/reminders/", json=reminder_data)
        assert res.status_code == 422


class TestGetReminder:
    def test_get_reminder(self, logged_client, test_reminders):
        reminder = test_reminders[0]
        res = logged_client.get(f"/reminders/{reminder.id}")
        assert res.status_code == 200
        reminder_data = schemas.Reminder(**res.json())
        assert reminder_data.id == reminder.id
        assert reminder_data.title == reminder.title
        assert reminder_data.user_id == reminder.user_id

    def test_get_reminder_not_found(self, logged_client):
        res = logged_client.get("/reminders/99999")
        assert res.status_code == 404
        assert res.json()["detail"] == "Reminder was not found"

    def test_get_reminder_unauthorized(self, client, test_reminders):
        reminder = test_reminders[0]
        res = client.get(f"/reminders/{reminder.id}")
        assert res.status_code == 401

    def test_get_reminder_forbidden(self, client, test_users, test_reminders):
        # Login as second user
        token = create_access_token(data={"user_id": test_users[1]["id"]})
        client.headers = {"Authorization": f"Bearer {token}"}

        # Try to access first user's reminder
        reminder = test_reminders[0]  # Belongs to first user
        res = client.get(f"/reminders/{reminder.id}")
        assert res.status_code == 403
        assert res.json()["detail"] == "Not allowed"


class TestGetAllReminders:
    def test_get_all_reminders(self, logged_client, test_reminders):
        res = logged_client.get("/reminders/")
        assert res.status_code == 200
        reminders = res.json()
        assert len(reminders) >= 1
        # All reminders should belong to the authenticated user
        for reminder in reminders:
            assert reminder["user_id"] == 1

    def test_get_reminders_filter_active(self, logged_client, test_reminders):
        # Test filtering active reminders
        res = logged_client.get("/reminders/?active=true")
        assert res.status_code == 200
        reminders = res.json()
        for reminder in reminders:
            assert reminder["is_active"] == True

        # Test filtering inactive reminders
        res = logged_client.get("/reminders/?active=false")
        assert res.status_code == 200
        reminders = res.json()
        for reminder in reminders:
            assert reminder["is_active"] == False

    def test_get_reminders_with_limit(self, logged_client, test_reminders):
        res = logged_client.get("/reminders/?limit=1")
        assert res.status_code == 200
        reminders = res.json()
        assert len(reminders) <= 1

    def test_get_reminders_unauthorized(self, client):
        res = client.get("/reminders/")
        assert res.status_code == 401


class TestUpdateReminder:
    def test_update_reminder(self, logged_client, test_reminders):
        reminder = test_reminders[0]
        update_data = {
            "title": "Updated reminder title",
            "amount": 999.99,
        }
        res = logged_client.put(f"/reminders/{reminder.id}", json=update_data)
        assert res.status_code == 200
        updated_reminder = schemas.Reminder(**res.json())
        assert updated_reminder.title == update_data["title"]
        assert updated_reminder.amount == update_data["amount"]
        assert updated_reminder.id == reminder.id

    def test_update_reminder_recurrence(self, logged_client, test_reminders):
        reminder = test_reminders[0]
        update_data = {"recurrence": "P7D"}  # Weekly recurrence
        res = logged_client.put(f"/reminders/{reminder.id}", json=update_data)
        assert res.status_code == 200
        updated_reminder = schemas.Reminder(**res.json())
        assert updated_reminder.recurrence is not None

    def test_update_reminder_not_found(self, logged_client):
        update_data = {"title": "Updated title"}
        res = logged_client.put("/reminders/99999", json=update_data)
        assert res.status_code == 404
        assert res.json()["detail"] == "Reminder was not found"

    def test_update_reminder_unauthorized(self, client, test_reminders):
        reminder = test_reminders[0]
        update_data = {"title": "Updated title"}
        res = client.put(f"/reminders/{reminder.id}", json=update_data)
        assert res.status_code == 401

    def test_update_reminder_forbidden(self, client, test_users, test_reminders):
        # Login as second user
        token = create_access_token(data={"user_id": test_users[1]["id"]})
        client.headers = {"Authorization": f"Bearer {token}"}

        # Try to update first user's reminder
        reminder = test_reminders[0]
        update_data = {"title": "Hacked title"}
        res = client.put(f"/reminders/{reminder.id}", json=update_data)
        assert res.status_code == 403
        assert res.json()["detail"] == "Not allowed"


class TestDeleteReminder:
    def test_delete_reminder(self, logged_client, test_reminders):
        reminder = test_reminders[0]
        res = logged_client.delete(f"/reminders/{reminder.id}")
        assert res.status_code == 204

        # Verify reminder is deleted
        res = logged_client.get(f"/reminders/{reminder.id}")
        assert res.status_code == 404

    def test_delete_reminder_not_found(self, logged_client):
        res = logged_client.delete("/reminders/99999")
        assert res.status_code == 404
        assert res.json()["detail"] == "Reminder was not found"

    def test_delete_reminder_unauthorized(self, client, test_reminders):
        reminder = test_reminders[0]
        res = client.delete(f"/reminders/{reminder.id}")
        assert res.status_code == 401

    def test_delete_reminder_forbidden(self, client, test_users, test_reminders):
        # Login as second user
        token = create_access_token(data={"user_id": test_users[1]["id"]})
        client.headers = {"Authorization": f"Bearer {token}"}

        # Try to delete first user's reminder
        reminder = test_reminders[0]
        res = client.delete(f"/reminders/{reminder.id}")
        assert res.status_code == 403
        assert res.json()["detail"] == "Not allowed"


class TestActivateDeactivateReminder:
    def test_activate_reminder(self, logged_client, test_reminders):
        # Find an inactive reminder or create one
        reminder = test_reminders[0]

        # First deactivate it
        logged_client.patch(f"/reminders/{reminder.id}/deactivate")

        # Then activate it
        res = logged_client.patch(f"/reminders/{reminder.id}/activate")
        assert res.status_code == 200
        activated_reminder = schemas.Reminder(**res.json())
        assert activated_reminder.is_active == True

    def test_deactivate_reminder(self, logged_client, test_reminders):
        reminder = test_reminders[0]
        res = logged_client.patch(f"/reminders/{reminder.id}/deactivate")
        assert res.status_code == 200
        deactivated_reminder = schemas.Reminder(**res.json())
        assert deactivated_reminder.is_active == False

    def test_activate_reminder_not_found(self, logged_client):
        res = logged_client.patch("/reminders/99999/activate")
        assert res.status_code == 404
        assert res.json()["detail"] == "Reminder was not found"

    def test_deactivate_reminder_not_found(self, logged_client):
        res = logged_client.patch("/reminders/99999/deactivate")
        assert res.status_code == 404
        assert res.json()["detail"] == "Reminder was not found"

    def test_activate_reminder_unauthorized(self, client, test_reminders):
        reminder = test_reminders[0]
        res = client.patch(f"/reminders/{reminder.id}/activate")
        assert res.status_code == 401

    def test_deactivate_reminder_unauthorized(self, client, test_reminders):
        reminder = test_reminders[0]
        res = client.patch(f"/reminders/{reminder.id}/deactivate")
        assert res.status_code == 401

    def test_activate_reminder_forbidden(self, client, test_users, test_reminders):
        # Login as second user
        token = create_access_token(data={"user_id": test_users[1]["id"]})
        client.headers = {"Authorization": f"Bearer {token}"}

        # Try to activate first user's reminder
        reminder = test_reminders[0]
        res = client.patch(f"/reminders/{reminder.id}/activate")
        assert res.status_code == 403
        assert res.json()["detail"] == "Not allowed"

    def test_deactivate_reminder_forbidden(self, client, test_users, test_reminders):
        # Login as second user
        token = create_access_token(data={"user_id": test_users[1]["id"]})
        client.headers = {"Authorization": f"Bearer {token}"}

        # Try to deactivate first user's reminder
        reminder = test_reminders[0]
        res = client.patch(f"/reminders/{reminder.id}/deactivate")
        assert res.status_code == 403
        assert res.json()["detail"] == "Not allowed"

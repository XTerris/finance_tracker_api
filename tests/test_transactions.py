from app import schemas
from typing import List


def test_get_all_transactions(logged_client, test_transactions):
    res = logged_client.get("/transactions/")
    assert res.status_code == 200
    assert len(res.json()) == len(test_transactions)
    res_data = [schemas.Transaction(**trans) for trans in res.json()]


from dataclasses import replace
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.fake import FakeUser


def _csv_file(name: str, text: str) -> tuple[str, BytesIO, str]:
    buf = BytesIO(text.encode("utf-8"))
    buf.seek(0)
    return (name, buf, "text/csv")


@pytest.fixture
def user(client: TestClient) -> FakeUser:
    user = FakeUser()
    response = client.post("/users", json=user.as_create_dict())
    assert response.status_code == 201
    username = response.json()["user"]["username"]
    return replace(user, id=response.json()["user"]["id"], username=username)


@pytest.fixture
def test_client(client: TestClient, user: FakeUser) -> TestClient:
    login_data = {"username": user.username, "password": user.password}
    login_response = client.post("/auth", data=login_data)
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_should_import_categories_and_list(test_client: TestClient) -> None:
    csv = """name,tags
Cinema,"Classic,Indie,Romance"
Books,"Fantasy,Mystery"
"""
    files = {"file": _csv_file("categories.csv", csv)}
    r = test_client.post("/reference/categories/import", files=files)
    assert r.status_code == 201

    r2 = test_client.get("/reference/categories")
    assert r2.status_code == 200
    cats = r2.json()["categories"]
    assert isinstance(cats, list)
    names = {c["name"] for c in cats}
    assert {"Cinema", "Books"}.issubset(names)


def test_should_import_references_list_and_get_single(test_client: TestClient) -> None:
    cat_csv = """name,tags
Cinema,"Classic,Romance"
"""
    _ = test_client.post(
        "/reference/categories/import",
        files={"file": _csv_file("categories.csv", cat_csv)},
    )

    rc = test_client.get("/reference/categories")
    assert rc.status_code == 200
    cats = rc.json()["categories"]
    cinema = next((c for c in cats if c["name"] == "Cinema"), None)
    assert cinema is not None
    cat_id = cinema["id"]

    ref_csv = """title,description,image_url,tags,founder,founded_year,category
Metropolis,Fritz Lang classic,https://x.m,"Classic",,1927,Film
Her,Love and AI,https://x.h,"Romance",Spike Jonze,2013,Film
"""
    r = test_client.post(
        f"/reference/{cat_id}/import",
        files={"file": _csv_file("refs.csv", ref_csv)},
    )
    assert r.status_code == 201

    rl = test_client.get(f"/reference/categories/{cat_id}/references")
    assert rl.status_code == 200
    refs = rl.json()["references"]
    assert isinstance(refs, list)
    assert len(refs) >= 2

    metro = next((r for r in refs if r["title"] == "Metropolis"), None)
    assert metro is not None
    rid = metro["id"]

    rs = test_client.get(f"/reference/references/{rid}")
    assert rs.status_code == 200
    ref = rs.json()["reference"]
    assert ref["title"] == "Metropolis"
    assert ref["image_url"] == "https://x.m"
    assert ref["tags"] == ["Classic"]


def test_should_reject_unsupported_file_type_on_categories(
    test_client: TestClient,
) -> None:
    files = {"file": ("bad.txt", BytesIO(b"nope"), "text/plain")}
    r = test_client.post("/reference/categories/import", files=files)
    assert r.status_code == 400


def test_should_return_404_for_unknown_reference(test_client: TestClient) -> None:
    rid = str(uuid4())
    r = test_client.get(f"/reference/references/{rid}")
    assert r.status_code == 404

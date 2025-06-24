from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Engine, insert, select
from sqlalchemy.orm import sessionmaker

import app.main
from dbschema.base import Base
from dbschema.schema import Subscriber

app.main.engine = create_engine("sqlite+pysqlite:///:testdb.db:", echo=True)
app.main.session = sessionmaker(app.main.engine, expire_on_commit=False)

client = TestClient(app.main.app)

@pytest.fixture()
def test_db():
    Base.metadata.create_all(app.main.engine)
    with app.main.session() as current_session:
        subscriber_1 = Subscriber(email="test@test123.com")
        subscriber_2 = Subscriber(email="petergriffin@test123.com")
        subscriber_3 = Subscriber(email="evil@evilevil.com")
        current_session.add_all([subscriber_1, subscriber_2, subscriber_3])
        current_session.commit()
    yield
    Base.metadata.drop_all(app.main.engine)


def test_get_all_subscribers(test_db):
    response = client.get("/subscribers/all")
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) == 3


def test_get_subscriber_by_id_exists(test_db):
    correct_id: str = ""
    with app.main.session() as current_session:
        query = select("*").where(Subscriber.email == "test@test123.com")
        results = current_session.execute(query).all()
        correct_id = str(UUID(results[0].id))
    response = client.get("/subscribers/{}".format(correct_id))
    assert response.status_code == HTTPStatus.OK
    assert response.json().get("id") == correct_id


def test_get_subscriber_by_id_does_not_exist(test_db):
    non_existent_id: str = str(uuid4())
    response = client.get("/subscribers/{}".format(non_existent_id))
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_add_new_subscriber(test_db):
    response = client.post("/subscribers/add",
                           json={"email": "newguy@test123.com"})
    assert response.status_code == HTTPStatus.CREATED


def test_add_existing_subscriber(test_db):
    response = client.post("/subscribers/add",
                           json={"email": "petergriffin@test123.com"})
    assert response.status_code == HTTPStatus.CONFLICT


def test_add_subscriber_non_valid_email(test_db):
    response = client.post("/subscribers/add",
                           json={"email": "<script> "
                                          "console.log('doing naughty things') "
                                          "</script>"}
                           )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

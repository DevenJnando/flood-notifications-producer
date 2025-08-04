import unittest
from http import HTTPStatus
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import app.connections.database_orm as orm
from app.main import app
from app.dbschema.base import Base
from app.dbschema.schema import Subscriber

client = TestClient(app)

mailing_list_engine = create_engine("sqlite+pysqlite:///:testdb.db:", echo=True)
session = sessionmaker(mailing_list_engine, expire_on_commit=False)

def get_session() -> sessionmaker:
    return session


class SubscriberTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[orm.get_session] = get_session
        Base.metadata.create_all(mailing_list_engine)
        with session() as current_session:
            subscriber_1 = Subscriber(email="test@test123.com")
            subscriber_2 = Subscriber(email="petergriffin@test123.com")
            subscriber_3 = Subscriber(email="evil@evilevil.com")
            current_session.add_all([subscriber_1, subscriber_2, subscriber_3])
            current_session.commit()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(mailing_list_engine)


    def test_get_all_subscribers(self):
        response = client.get("/subscribers/all")
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) == 3 or len(response.json()) == 4


    def test_get_subscriber_by_id_exists(self):
        correct_id: str = ""
        with session() as current_session:
            query = select("*").where(Subscriber.email == "test@test123.com")
            results = current_session.execute(query).all()
            correct_id = str(UUID(results[0].id))
        response = client.get("/subscribers/get/id/{}".format(correct_id))
        assert response.status_code == HTTPStatus.OK
        assert response.json().get("id") == correct_id


    def test_get_subscriber_by_id_does_not_exist(self):
        non_existent_id: str = str(uuid4())
        response = client.get("/subscribers/get/id/{}".format(non_existent_id))
        assert response.status_code == HTTPStatus.NOT_FOUND


    def test_get_subscriber_by_email_exists(self):
        correct_email: str = ""
        with session() as current_session:
            query = select("*").where(Subscriber.email == "test@test123.com")
            results = current_session.execute(query).all()
            correct_email = results[0].email
        response = client.get("/subscribers/get/email/{}".format(correct_email))
        assert response.status_code == HTTPStatus.OK
        assert response.json().get("email") == correct_email


    def test_get_subscriber_by_email_does_not_exist(self):
        non_existent_email: str = "itwasmadeup@byawriter.com"
        response = client.get("/subscribers/get/email/{}".format(non_existent_email))
        assert response.status_code == HTTPStatus.NOT_FOUND


    def test_add_new_subscriber(self):
        response = client.post("/subscribers/add",
                               data={"email": "newguy@newmail.com",
                                     "postcodes": [
                                         "G769DQ",
                                         "BT97FX"
                                     ]})
        assert response.status_code == HTTPStatus.CREATED


    def test_add_existing_subscriber(self):
        response = client.post("/subscribers/add",
                               data={"email": "petergriffin@test123.com",
                                     "postcodes": [
                                         "G769DQ",
                                         "BT97FX"
                                     ]})
        assert response.status_code == HTTPStatus.CONFLICT


    def test_add_subscriber_non_valid_email(self):
        response = client.post("/subscribers/add",
                               data={"email": "<script> "
                                              "console.log('doing naughty things') "
                                              "</script>",
                                     "postcodes": [
                                         "G769DQ",
                                         "BT97FX"
                                     ]
                                     }
                               )
        assert response.status_code == HTTPStatus.NOT_ACCEPTABLE

if __name__ == "__main__":
    unittest.main()

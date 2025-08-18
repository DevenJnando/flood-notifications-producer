import os
import unittest
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.dbschema.base import Base
from app.dbschema.schema import Subscriber, Postcode
from app.services.subscriber_service import (get_all_subscribers,
                                             get_subscriber_by_id,
                                             get_subscriber_by_email,
                                             get_subscribers_by_postcode,
                                             add_new_subscriber, get_all_subscribers_by_postcodes
                                             )
from app.models.pydantic_models.subscriber_form import SubscriberForm

from fastapi import HTTPException

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

mailing_list_engine = create_engine("sqlite+pysqlite:///" + root_dir + "/mock-database/:testdb.db:", echo=True)
session = sessionmaker(mailing_list_engine, expire_on_commit=False)

def get_session() -> sessionmaker:
    return session


class SubscriberTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(mailing_list_engine)
        with session() as current_session:
            subscriber_1 = Subscriber(email="test@test123.com")
            subscriber_2 = Subscriber(email="petergriffin@test123.com")
            subscriber_3 = Subscriber(email="evil@evilevil.com")
            postcode_1 = Postcode(postcode="G769DQ", subscriber=subscriber_2)
            subscriber_2.postcodes.append(postcode_1)
            current_session.add_all([subscriber_1, subscriber_2, subscriber_3, postcode_1])
            current_session.commit()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(mailing_list_engine)


    def test_get_all_subscribers(self):
        subscribers = get_all_subscribers(session=session)
        assert len(subscribers) == 3 or len(subscribers) == 4


    def test_get_subscriber_by_id_exists(self):
        correct_id: UUID
        with session() as current_session:
            query = select("*").where(Subscriber.email == "test@test123.com")
            results = current_session.execute(query).all()
            correct_id = UUID(results[0].id)
        subscriber = get_subscriber_by_id(session=session, subscriber_id=correct_id)
        assert subscriber.id == correct_id


    def test_get_subscriber_by_id_does_not_exist(self):
        non_existent_id: UUID = uuid4()
        self.assertRaises(HTTPException, lambda: get_subscriber_by_id(session=session, subscriber_id=non_existent_id))


    def test_get_subscriber_by_email_exists(self):
        correct_email: str = ""
        with session() as current_session:
            query = select("*").where(Subscriber.email == "test@test123.com")
            results = current_session.execute(query).all()
            correct_email = results[0].email
        subscriber = get_subscriber_by_email(session=session, subscriber_email=correct_email)
        assert subscriber.email == correct_email


    def test_get_subscriber_by_email_does_not_exist(self):
        non_existent_email: str = "itwasmadeup@byawriter.com"
        self.assertRaises(HTTPException, lambda: get_subscriber_by_email(session=session, subscriber_email=non_existent_email))


    def test_get_subscriber_by_postcode_exists(self):
        postcode = "G769DQ"
        list_of_subscribers: list[Subscriber] = get_subscribers_by_postcode(session=session, postcode=postcode)
        assert len(list_of_subscribers) == 1 or len(list_of_subscribers) == 2
        subscriber: Subscriber = list_of_subscribers[0]
        assert subscriber.email == "petergriffin@test123.com" or subscriber.email == "newguy@newmail.com"


    def test_get_subscriber_by_postcode_does_not_exist(self):
        postcode = "DL91DY"
        self.assertRaises(HTTPException, lambda: get_subscribers_by_postcode(session=session, postcode=postcode))


    def test_get_subscribers_by_postcodes_exists(self):
        postcodes: set[str] = {"G769DQ", "BT97FX"}
        list_of_subscribers: list[Subscriber] = get_all_subscribers_by_postcodes(session=session, postcodes=postcodes)
        assert len(list_of_subscribers) == 1 or len(list_of_subscribers) == 3
        for subscriber in list_of_subscribers:
            assert subscriber.email == "petergriffin@test123.com" or subscriber.email == "newguy@newmail.com"


    def test_get_subscriber_by_postcodes_do_not_exist(self):
        postcode: set[str] = {"DL91DY", "LAY8TF"}
        list_of_subscribers: list[Subscriber] = get_all_subscribers_by_postcodes(session=session, postcodes=postcode)
        assert len(list_of_subscribers) == 0


    def test_add_new_subscriber(self):
        email = "newguy@newmail.com"
        subscriber_form = SubscriberForm(email=email,
                                     postcodes=[
                                         "G769DQ",
                                         "BT97FX"
                                     ])
        add_new_subscriber(session=session, subscriber_form=subscriber_form)
        new_subscriber = get_subscriber_by_email(session=session, subscriber_email=email)
        assert new_subscriber.email == email


    def test_add_existing_subscriber(self):
        email = "petergriffin@test123.com"
        subscriber_form = SubscriberForm(email=email,
                                         postcodes=[
                                             "G769DQ",
                                             "BT97FX"
                                         ])
        self.assertRaises(HTTPException, lambda: add_new_subscriber(session=session, subscriber_form=subscriber_form))


    def test_add_subscriber_non_valid_email(self):
        email = "<script> "\
                "console.log('doing naughty things') "\
                "</script>"

        subscriber_form = SubscriberForm(email=email,
                                         postcodes=[
                                             "G769DQ",
                                             "BT97FX"
                                         ])
        self.assertRaises(HTTPException, lambda: add_new_subscriber(session=session, subscriber_form=subscriber_form))


if __name__ == "__main__":
    unittest.main()

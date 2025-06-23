from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from dbschema.schema import Subscriber


def get_all_subscribers(session: sessionmaker) -> List[Subscriber | None]:
    subscribers: Sequence = []
    subscriber_objects: List[Subscriber] = []
    with session.begin() as session:
        statement = select(Subscriber.id, Subscriber.email)
        subscribers = session.execute(statement).all()
    for subscriber in subscribers:
        subscriber_object = Subscriber(id=subscriber.id, email=subscriber.email)
        subscriber_objects.append(subscriber_object)
    return subscriber_objects
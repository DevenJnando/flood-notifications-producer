from http import HTTPStatus
from typing import List, Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from dbschema.schema import Subscriber


def get_all_subscribers(session: sessionmaker) -> List[Subscriber | None]:
    subscribers: Sequence = []
    subscriber_objects: List[Subscriber] = []
    with session.begin() as session:
        query = select(Subscriber.id, Subscriber.email)
        subscribers = session.execute(query).all()
    for subscriber in subscribers:
        subscriber_object = Subscriber(id=subscriber.id, email=subscriber.email)
        subscriber_objects.append(subscriber_object)
    return subscriber_objects


def get_subscriber_by_id(session: sessionmaker, subscriber_id: UUID) -> Subscriber | None:
    with session.begin() as session:
        subscriber: Subscriber | None = session.get(Subscriber, subscriber_id)
        if subscriber is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="Subscriber with given id {} not found"
                                .format(subscriber_id))
        return subscriber

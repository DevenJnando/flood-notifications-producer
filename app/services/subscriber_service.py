from http import HTTPStatus
from typing import List, Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from email_validator import validate_email, EmailNotValidError, ValidatedEmail

from app.dbschema.schema import Subscriber, Postcode
from app.models.subscriber_form import SubscriberForm


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


def get_subscriber_by_email(session: sessionmaker, subscriber_email: str) -> Subscriber | None:
    with session.begin() as session:
        subscriber: Subscriber | None = session.query(Subscriber).filter_by(email=subscriber_email).scalar()
        if subscriber is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="Subscriber with given email {} not found"
                                .format(subscriber_email))
        return subscriber


def add_new_subscriber(session: sessionmaker, subscriber_form: SubscriberForm) -> None:
    try:
        with session() as session:
            subscriber_email: ValidatedEmail = validate_email(subscriber_form.email, check_deliverability=False)
            normalized_email: str = subscriber_email.normalized
            exists: bool = session.query(Subscriber).filter_by(email=normalized_email).scalar() is not None
            if exists:
                raise HTTPException(status_code=HTTPStatus.CONFLICT,
                                    detail="Subscriber with given email {} already exists"
                                    .format(normalized_email))
            subscriber = Subscriber(email=normalized_email)
            for postcode in subscriber_form.postcodes:
                postcode_object = Postcode(postcode=postcode)
                subscriber.postcodes.append(postcode_object)
            session.add(subscriber)
            session.commit()
    except EmailNotValidError:
        raise HTTPException(status_code=HTTPStatus.NOT_ACCEPTABLE,
                            detail="The entered email {} is invalid".format(subscriber_form.email)
                            )

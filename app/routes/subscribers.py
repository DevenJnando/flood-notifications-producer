from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Depends
from sqlalchemy.orm.session import sessionmaker

from app.models.pydantic_models.subscriber_form import SubscriberForm
from app.connections.database_orm import get_session
from app.services.subscriber_service import (get_all_subscribers,
                                             get_subscriber_by_id,
                                             get_subscriber_by_email, add_new_subscriber)

router = APIRouter()

@router.get("/subscribers/all")
async def handle_get_all_subscribers(session: Annotated[sessionmaker, Depends(get_session)]):
    return get_all_subscribers(session)


@router.post("/subscribers/add", status_code=HTTPStatus.CREATED.value)
async def handle_add_subscriber(session: Annotated[sessionmaker, Depends(get_session)],
                                subscriber_form: Annotated[SubscriberForm, Form()]):
    add_new_subscriber(session, subscriber_form)


@router.get("/subscribers/get/id/{subscriber_id}")
async def handle_get_subscriber_by_id(session: Annotated[sessionmaker, Depends(get_session)],
                                      subscriber_id: UUID):
    return get_subscriber_by_id(session, subscriber_id)


@router.get("/subscribers/get/email/{subscriber_email}")
async def handle_get_subscriber_by_email(session: Annotated[sessionmaker, Depends(get_session)],
                                         subscriber_email: str):
    return get_subscriber_by_email(session, subscriber_email)
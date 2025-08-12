from pydantic import BaseModel

class MetaData(BaseModel):
    publisher: str
    licence: str
    documentation: str
    version: str
    comment: str
    hasFormat: list[str]
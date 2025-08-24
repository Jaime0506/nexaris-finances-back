from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

metadata = MetaData(schema=settings.PG_SCHEMA)

class Base(DeclarativeBase):
    metadata = metadata
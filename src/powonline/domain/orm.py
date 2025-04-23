from sqlalchemy.orm import mapper
import uuid
from sqlalchemy import MetaData, Table, Column, Unicode, Uuid, DateTime

from . import registration


metadata = MetaData()

event = Table(  #(2)
    "event",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4),
    Column("name", Unicode(255)),
    Column("start", DateTime(timezone=True), nullable=False),
    Column("end", DateTime(timezone=True), nullable=False),
)

def start_mappers():
    lines_mapper = mapper(registration.Event, event)
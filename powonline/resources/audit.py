from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import model, schema
from powonline.auth import User, get_user
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/auditlog", tags=["audit"])


@ROUTER.get("")
async def get(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[schema.AuditLogEntry]:
    auth_user.require_permission("view_audit_log")
    query = select(model.AuditLog).order_by(model.AuditLog.timestamp.desc())
    result = await session.execute(query)
    output = []
    for row in result.scalars():
        output.append(
            schema.AuditLogEntry(
                timestamp=row.timestamp,
                username=row.username or "",
                type=row.type_,
                message=row.message,
            )
        )
    return output

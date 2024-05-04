import logging
import re
import unicodedata
from configparser import ConfigParser
from datetime import datetime, timezone
from io import BytesIO
from os import makedirs, stat
from os.path import basename, join
from posixpath import splitext
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from PIL import ExifTags, Image
from powonline.auth import User, get_user
from powonline.config import default
from powonline.dependencies import get_db, get_pusher
from powonline.exc import AccessDenied, AuthDeniedReason, NotFound
from powonline.model import Upload
from powonline.pusher import PusherWrapper
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema

ROUTER = APIRouter(prefix="", tags=["files", "uploads"])
LOG = logging.getLogger(__name__)


EXIF_TAGS = ExifTags.TAGS
FILE_MAPPINGS = {
    "gif": ("gif", "image/gif"),
    "jpg": ("jpeg", "image/jpeg"),
    "jpeg": ("jpeg", "image/jpeg"),
    "png": ("png", "image/png"),
}


def allowed_file(filename: str) -> bool:
    name, ext = splitext(filename)
    return ext.lower() in FILE_MAPPINGS


def secure_filename(filename):
    filename = (
        unicodedata.normalize("NFKD", filename)
        .encode("ASCII", "ignore")
        .decode("ASCII")
    )
    filename = re.sub(r"[^\w\s-]", "", filename).strip().lower()
    filename = re.sub(r"[-\s]+", "-", filename)
    return filename


def upload_to_json(
    request: Request, data_folder: str, db_instance: Upload
) -> schema.UploadSchema | None:
    """
    Convert a DB-instance of an upload to a JSONifiable dictionary
    """
    file_url = request.url_for(
        "api.get_file", uuid=db_instance.uuid, _external=True, _scheme="https"
    )
    tn_url = request.url_for(
        "api.get_file",
        uuid=db_instance.uuid,
        size=256,
        _external=True,
        _scheme="https",
    )
    tiny_url = request.url_for(
        "api.get_file",
        uuid=db_instance.uuid,
        size=64,
        _external=True,
        _scheme="https",
    )

    fullname = join(data_folder, db_instance.filename or "")

    try:
        mtime_unix = stat(fullname).st_mtime
    except FileNotFoundError:
        LOG.warning("Missing file %r (was in DB but not on disk)!", fullname)
        return None
    mtime = datetime.fromtimestamp(mtime_unix, timezone.utc)

    return schema.UploadSchema(
        uuid=db_instance.uuid,
        href=str(file_url),
        thumbnail=str(tn_url),
        tiny=str(tiny_url),
        name=basename(db_instance.filename or ""),
        when=mtime,
    )


def _rotated(fullname: str):
    im = Image.open(fullname)
    o_id = {v: k for k, v in EXIF_TAGS.items()}["Orientation"]
    orientation = im.getexif().get(o_id)
    if not orientation:
        return im
    if orientation == 3:
        im = im.rotate(180, expand=True)
    elif orientation == 6:
        im = im.rotate(270, expand=True)
    elif orientation == 8:
        im = im.rotate(90, expand=True)
    return im


def _thumbnail(fullname: str, size: int):
    im = _rotated(fullname)

    # Limit the size to an upper-bound. This prevents users from enlarging
    # files to inhumane sizes triggering a DoS
    if size and size < 4000:
        im.thumbnail((size, size))

    _, extension = fullname.rsplit(".", 1)
    pillow_type, mediatype = FILE_MAPPINGS[extension.lower()]
    output = BytesIO()
    im.save(output, format=pillow_type)
    return output, mediatype


@ROUTER.post("/upload")
async def create_upload(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    config: Annotated[ConfigParser, Depends(default)],
    pusher: Annotated[PusherWrapper, Depends(get_pusher)],
    request: Request,
    upload_file: UploadFile = File(),
):
    data_folder = config.get(
        "app", "upload_folder", fallback=core.Upload.FALLBACK_FOLDER
    )
    if not upload_file.filename:
        return Response("No file selected", 400)

    if upload_file and allowed_file(upload_file.filename):
        filename = secure_filename(upload_file.filename)
        try:
            makedirs(join(data_folder, auth_user.name))
        except FileExistsError:
            pass
        relative_target = join(auth_user.name, filename)
        target = join(data_folder, relative_target)
        with open(target, "wb") as target_file_object:
            target_file_object.write(upload_file.file.read())

        db_instance = await core.Upload.store(
            session, auth_user.name, relative_target
        )

        file_data = upload_to_json(request, data_folder, db_instance)
        if not file_data:
            return Response("Failed to store file", 500)
        response = Response(
            file_data,
            headers={"Location": file_data.href},
            status_code=201,
        )
        pusher.send_file_event("file-added", file_data)
        return response

    return Response("The given file is not allowed", 400)


async def _get_public(
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    data_folder: str,
) -> list[schema.UploadSchema]:
    """
    Return files for a public request (f.ex. image gallery)
    """
    output: list[schema.UploadSchema] = []
    files = await core.Upload.all(session)
    for item in files:
        json_data = upload_to_json(request, data_folder, item)
        if json_data:
            output.append(json_data)
    return output


async def _get_private(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User,
    request: Request,
    data_folder: str,
) -> list[schema.UploadSchema]:
    """
    Return files for a private request (f.ex. manageing uploads)
    """
    all_permissions = user.permissions
    output: dict[str, list[schema.UploadSchema]] = {}
    if "admin_files" in all_permissions:
        files = await core.Upload.all(session)
        for item in files:
            output_files = output.setdefault(item.username, [])
            json_data = upload_to_json(request, data_folder, item)
            if json_data:
                output_files.append(json_data)
    else:
        files = await core.Upload.list(session, user.name)
        output_files = []
        for item in files:
            json_data = upload_to_json(request, data_folder, item)
            if json_data:
                output_files.append(json_data)
        output["self"] = output_files
    return output   # TODO: Align return type of both "private" and "public" uploads


@ROUTER.get("/upload")
async def query_uploads(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    config: Annotated[ConfigParser, Depends(default)],
    public: bool = False,
) -> list[schema.UploadSchema]:
    """
    Retrieve a list of uploads
    """
    data_folder = config.get(
        "app", "upload_folder", fallback=core.Upload.FALLBACK_FOLDER
    )
    if public:
        return await _get_public(session, request, data_folder)
    return await _get_private(session, auth_user, request, data_folder)


@ROUTER.get("/upload/{uuid}", name="api.get_file")
async def get_file(
    session: Annotated[AsyncSession, Depends(get_db)],
    uuid: UUID,
    config: Annotated[ConfigParser, Depends(default)],
    size: int = 0,
):
    """
    Retrieve a single file
    """
    data_folder = config.get(
        "app", "upload_folder", fallback=core.Upload.FALLBACK_FOLDER
    )
    db_instance = await core.Upload.by_id(session, uuid)
    if not db_instance:
        raise NotFound("File not found")

    fullname = join(data_folder, db_instance.filename)
    thumbnail, mediatype = _thumbnail(fullname, size)
    output = Response(thumbnail.getvalue(), media_type=mediatype)
    output.headers[
        "Content-Disposition"
    ] = f"inline; filename=thn_{basename(db_instance.filename)}"
    return output


@ROUTER.delete("/upload/{uuid}", name="api.delete_file")
async def delete_file(
    session: Annotated[AsyncSession, Depends(get_db)],
    uuid: UUID,
    user: User,
    request: Request,
    config: Annotated[ConfigParser, Depends(default)],
    pusher: Annotated[PusherWrapper, Depends(get_pusher)],
):
    """
    Retrieve a single file
    """
    db_instance = await core.Upload.by_id(session, uuid)
    if not db_instance:
        raise NotFound("File not found")
    all_permissions = user.permissions
    if (
        "admin_files" not in all_permissions
        and user.name != db_instance.username
    ):
        return AccessDenied("Access Denied", AuthDeniedReason.ACCESS_DENIED)
    data_folder = config.get(
        "app", "upload_folder", fallback=core.Upload.FALLBACK_FOLDER
    )
    await core.Upload.delete(session, data_folder, db_instance)
    pusher.send_file_event("file-deleted", {"id": uuid})
    return "OK"

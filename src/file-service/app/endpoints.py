from fastapi import APIRouter, UploadFile, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from bson import ObjectId
from gridfs.errors import NoFile

from app.config import settings

router = APIRouter()

client = AsyncIOMotorClient(str(settings.MONGODB_URL), serverSelectionTimeoutMS=3000)
gfs_bucket = AsyncIOMotorGridFSBucket(client.files)


@router.post("/upload")
async def upload_file(file: UploadFile):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file")

        async with gfs_bucket.open_upload_stream(filename=file.filename) as stream:
            await stream.write(contents)
            file_id = stream._id

        return {"file_id": str(file_id), "filename": file.filename}

    except Exception:
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    try:
        grid_out = await gfs_bucket.open_download_stream(ObjectId(file_id))
        data = await grid_out.read()
        filename = grid_out.filename or f"{file_id}"

        return {
            "filename": filename,
            "file_id": file_id,
            "content_base64": data.decode("latin1")
        }

    except NoFile:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception:
        raise HTTPException(status_code=500)

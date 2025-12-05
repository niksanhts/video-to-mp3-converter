import requests
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import require_token
from app.api.publisher import rabbitmq_publisher
from app.core.config import settings

router = APIRouter()

FILE_STORAGE_URL = settings.FILE_STORAGE_URL


@router.post("/")
def upload_video(video: UploadFile, token: dict[str, str] = Depends(require_token)):
    if not video or not video.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    try:
        files = {"file": (video.filename, video.file.read())}
        response = requests.post(f"{FILE_STORAGE_URL}/upload", files=files, timeout=60)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="File storage service failed")

        file_info = response.json()
        file_id = file_info["file_id"]

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="File upload failed")

    # Публикуем сообщение в RabbitMQ
    try:
        rabbitmq_publisher.publish({
            "video_fid": str(file_id),
            "mp3_fid": None,
            "email": token["email"],
        })
    except Exception as e:
        print(e)
        # Попытка удалить файл через file-storage-service при ошибке публикации
        try:
            requests.delete(f"{FILE_STORAGE_URL}/{file_id}", timeout=10)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Publishing failed")

    return {"file_id": str(file_id), "filename": video.filename}


@router.get("/{file_id}")
def download_video(file_id: str):
    try:
        response = requests.get(f"{FILE_STORAGE_URL}/{file_id}", timeout=60)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="File not found")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="File storage service error")

        file_info = response.json()
        content = file_info.get("content_base64")
        filename = file_info.get("filename", file_id)

        # Временный файл для FileResponse
        temp_file = temp_file.NamedTemporaryFile(delete=False)
        temp_file.write(content.encode("latin1"))
        temp_file.close()

        return FileResponse(temp_file.name, filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Download failed")
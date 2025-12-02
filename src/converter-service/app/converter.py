import json
import os
import tempfile

import gridfs
from moviepy import VideoFileClip
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import settings
from app.publisher import rabbitmq_publisher
from app import logger

client = MongoClient(settings.MONGODB_URL)
gfs_bucket = gridfs.GridFS(client.videos)
gfs_bucket_mp3 = gridfs.GridFS(client.mp3s)


def convert(message):
    try:
        message = json.loads(message)
        logger.info(f"Starting conversion for message: {message}")

        with tempfile.NamedTemporaryFile() as tf:
            file_id = ObjectId(message.get("video_fid"))
            logger.info(f"Fetching video with ID: {file_id}")

            # Get video content
            try:
                video_data = gfs_bucket.get(file_id)
                logger.info("Video fetched successfully")
            except PyMongoError as err:
                logger.error(f"Failed to fetch video from GridFS: {err}", exc_info=True)
                return "Failed to download the video"
            except Exception as err:
                logger.error(f"Unexpected error fetching video: {err}", exc_info=True)
                return "Failed to download the video"

            # Write video contents to temp file
            try:
                tf.write(video_data.read())
                tf.flush()
                logger.info("Video data written to temporary file")
            except Exception as err:
                logger.error(f"Failed to write video to temp file: {err}", exc_info=True)
                return "Failed to write video to temp file"

            # Extract audio
            try:
                audio = VideoFileClip(tf.name).audio
                logger.info("Audio extracted from video")
            except Exception as err:
                logger.error(f"Failed to extract audio from video: {err}", exc_info=True)
                return "Failed to extract audio"

            # Create temporary MP3 file
            tf_mp3_path = os.path.join(tempfile.gettempdir(), f"{message['video_fid']}.mp3")
            try:
                audio.write_audiofile(tf_mp3_path)
                logger.info(f"Audio written to MP3 file: {tf_mp3_path}")
            except Exception as err:
                logger.error(f"Failed to write MP3 file: {err}", exc_info=True)
                return "Failed to write MP3 file"

            # Save MP3 to GridFS
            try:
                with open(tf_mp3_path, "rb") as f:
                    data = f.read()
                    fid = gfs_bucket_mp3.put(data)
                logger.info(f"MP3 uploaded to GridFS with ID: {fid}")
            except PyMongoError as err:
                logger.error(f"Failed to upload MP3 to GridFS: {err}", exc_info=True)
                return "Failed to upload the mp3"
            except Exception as err:
                logger.error(f"Unexpected error uploading MP3: {err}", exc_info=True)
                return "Failed to upload the mp3"
            finally:
                # Remove temporary MP3 file
                try:
                    os.remove(tf_mp3_path)
                    logger.info(f"Temporary MP3 file removed: {tf_mp3_path}")
                except Exception:
                    logger.warning(f"Failed to remove temporary MP3 file: {tf_mp3_path}")

            message["mp3_fid"] = str(fid)

            # Publish to RabbitMQ
            try:
                rabbitmq_publisher.publish(message)
                logger.info("Message published successfully to RabbitMQ")
            except Exception as err:
                logger.error(f"Failed to publish message: {err}", exc_info=True)
                try:
                    gfs_bucket_mp3.delete(fid)
                    logger.info(f"Deleted MP3 from GridFS due to publish failure: {fid}")
                except Exception:
                    logger.warning(f"Failed to delete MP3 after publish failure: {fid}")
                return "Failed to publish message"

    except json.JSONDecodeError:
        logger.error("Invalid JSON in message", exc_info=True)
        return "Invalid JSON in message"
    except Exception as err:
        logger.error(f"An unexpected error occurred during conversion: {err}", exc_info=True)
        return "An error occurred during conversion"

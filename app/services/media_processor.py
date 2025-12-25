"""
Media processing service for thumbnail generation and optimization.
"""

import io
import tempfile
from typing import Optional, Tuple
from uuid import UUID
from PIL import Image
from app.services.memory_service import get_media_by_id, update_media_processing_status
from app.db.supabase import get_supabase_service_client
from app.config import get_settings
from app.utils.media import is_image, is_video


settings = get_settings()


async def process_media_async(media_id: UUID) -> None:
    """
    Process media file asynchronously: generate thumbnail, optimize, extract metadata.
    
    This function is called as a background task.
    
    Args:
        media_id: Media record ID
    """
    try:
        # Update status to processing
        await update_media_processing_status(media_id, "processing")
        
        # Get media record
        media = await get_media_by_id(media_id)
        if not media:
            await update_media_processing_status(
                media_id,
                "failed",
                metadata={"error": "Media record not found"}
            )
            return
        
        # Process based on MIME type
        if is_image(media.mime_type):
            await process_image(media)
        elif is_video(media.mime_type):
            await process_video(media)
        else:
            await update_media_processing_status(
                media_id,
                "failed",
                metadata={"error": f"Unsupported media type: {media.mime_type}"}
            )
            
    except Exception as e:
        # Update status to failed
        await update_media_processing_status(
            media_id,
            "failed",
            metadata={"error": str(e)}
        )
        raise


async def process_image(media) -> None:
    """
    Process image: generate thumbnail and extract metadata.
    
    Args:
        media: MemoryMedia object
    """
    service_client = get_supabase_service_client()
    
    try:
        # Download image from storage
        image_data = await download_from_storage(media.storage_path)
        if not image_data:
            raise ValueError("Failed to download image from storage")
        
        # Open image with PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Extract metadata
        width, height = image.size
        metadata = {
            "format": image.format,
            "mode": image.mode
        }
        
        # Extract EXIF data if available
        if hasattr(image, '_getexif') and image._getexif():
            metadata["exif"] = dict(image._getexif())
        
        # Generate thumbnail
        thumbnail = generate_thumbnail(image, settings.media_thumbnail_size)
        
        # Upload thumbnail to storage
        thumbnail_path = f"{media.storage_path.rsplit('.', 1)[0]}_thumb.jpg"
        thumbnail_data = io.BytesIO()
        thumbnail.save(thumbnail_data, format="JPEG", quality=85)
        thumbnail_data.seek(0)
        
        await upload_to_storage(thumbnail_path, thumbnail_data.getvalue(), "image/jpeg")
        
        # Update media record
        await update_media_processing_status(
            media.id,
            "completed",
            thumbnail_path=thumbnail_path,
            width=width,
            height=height,
            metadata=metadata
        )
        
    except Exception as e:
        await update_media_processing_status(
            media.id,
            "failed",
            metadata={"error": f"Image processing failed: {str(e)}"}
        )
        raise


async def process_video(media) -> None:
    """
    Process video: extract metadata and generate thumbnail.
    
    Args:
        media: MemoryMedia object
    """
    # For MVP, we'll extract basic metadata
    # Video thumbnail extraction requires ffmpeg (optional enhancement)
    
    try:
        # Download video to get file size and basic info
        # In production, use ffmpeg to extract frame and metadata
        metadata = {
            "note": "Video processing requires ffmpeg for full metadata extraction"
        }
        
        # For now, mark as completed without thumbnail
        # Frontend can use video's first frame or placeholder
        await update_media_processing_status(
            media.id,
            "completed",
            metadata=metadata
        )
        
    except Exception as e:
        await update_media_processing_status(
            media.id,
            "failed",
            metadata={"error": f"Video processing failed: {str(e)}"}
        )
        raise


def generate_thumbnail(image: Image.Image, max_size: int) -> Image.Image:
    """
    Generate thumbnail from image.
    
    Args:
        image: PIL Image object
        max_size: Maximum dimension (width or height)
    
    Returns:
        Thumbnail Image
    """
    # Calculate thumbnail size maintaining aspect ratio
    width, height = image.size
    
    if width > height:
        if width > max_size:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            return image.copy()
    else:
        if height > max_size:
            new_height = max_size
            new_width = int(width * (max_size / height))
        else:
            return image.copy()
    
    # Resize image
    thumbnail = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return thumbnail


async def download_from_storage(storage_path: str) -> Optional[bytes]:
    """
    Download file from Supabase Storage.
    
    Args:
        storage_path: Path to file in storage
    
    Returns:
        File data as bytes or None if failed
    """
    service_client = get_supabase_service_client()
    
    try:
        # Extract bucket and path
        # Path format: {family_unit_id}/{memory_id}/{file_name}
        path_parts = storage_path.split("/", 1)
        if len(path_parts) < 2:
            return None
        
        bucket = "memories"
        file_path = path_parts[1] if len(path_parts) > 1 else storage_path
        
        # Download file
        response = service_client.storage.from_(bucket).download(file_path)
        
        if isinstance(response, bytes):
            return response
        elif hasattr(response, 'content'):
            return response.content
        else:
            return None
            
    except Exception as e:
        print(f"Error downloading from storage: {e}")
        return None


async def upload_to_storage(storage_path: str, file_data: bytes, content_type: str) -> bool:
    """
    Upload file to Supabase Storage.
    
    Args:
        storage_path: Path to store file
        file_data: File data as bytes
        content_type: MIME type
    
    Returns:
        True if successful, False otherwise
    """
    service_client = get_supabase_service_client()
    
    try:
        # Extract bucket and path
        path_parts = storage_path.split("/", 1)
        if len(path_parts) < 2:
            return False
        
        bucket = "memories"
        file_path = path_parts[1] if len(path_parts) > 1 else storage_path
        
        # Upload file
        service_client.storage.from_(bucket).upload(
            file_path,
            file_data,
            file_options={"content-type": content_type}
        )
        
        return True
        
    except Exception as e:
        print(f"Error uploading to storage: {e}")
        return False


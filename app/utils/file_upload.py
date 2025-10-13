import os
import uuid
import mimetypes
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException
from pathlib import Path

# Allowed file types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
}

ALLOWED_FILE_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'application/zip',
    'application/x-rar-compressed'
}

# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE = 50 * 1024 * 1024   # 50MB

class FileUploadManager:
    def __init__(self):
        self.base_path = Path("static/chat_files")
        self.images_path = self.base_path / "images"
        self.files_path = self.base_path / "files"
        
        # Create directories if they don't exist
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.files_path.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: UploadFile, is_image: bool = False) -> Tuple[bool, str]:
        """Validate uploaded file"""
        # Check file size
        file_size = 0
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        max_size = MAX_IMAGE_SIZE if is_image else MAX_FILE_SIZE
        if file_size > max_size:
            size_mb = max_size / (1024 * 1024)
            return False, f"File too large. Maximum size: {size_mb:.1f}MB"
        
        # Check MIME type
        mime_type = file.content_type
        allowed_types = ALLOWED_IMAGE_TYPES if is_image else ALLOWED_FILE_TYPES
        
        if mime_type not in allowed_types:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        
        return True, "Valid"
    
    def generate_filename(self, original_filename: str) -> str:
        """Generate unique filename"""
        file_extension = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"
    
    async def upload_file(self, file: UploadFile, is_image: bool = False) -> dict:
        """Upload file and return file info"""
        # Validate file
        is_valid, error_msg = self.validate_file(file, is_image)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Generate unique filename
        unique_filename = self.generate_filename(file.filename)
        
        # Determine upload path
        upload_path = self.images_path if is_image else self.files_path
        file_path = upload_path / unique_filename
        
        # Get file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = file.content_type
        
        return {
            "file_name": file.filename,
            "file_path": f"chat_files/{'images' if is_image else 'files'}/{unique_filename}",
            "file_size": file_size,
            "mime_type": mime_type
        }
    
    # Multiple file upload method removed - using WebSocket only for file uploads
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            full_path = self.base_path / file_path.replace("chat_files/", "")
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def get_file_url(self, file_path: str) -> str:
        """Get full URL for file"""
        return f"/static/{file_path}"

# Global file upload manager
file_upload_manager = FileUploadManager()

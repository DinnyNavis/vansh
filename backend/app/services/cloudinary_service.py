"""
Cloudinary Image Service — Permanent image hosting and optimization.
"""

import os
import logging
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

logger = logging.getLogger(__name__)

class CloudinaryService:
    def __init__(self, cloud_name, api_key, api_secret):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        
        if not all([cloud_name, api_key, api_secret]):
            logger.warning("Cloudinary credentials missing. Uploads will fail.")
            
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )

    def upload_image(self, file_path, folder="vansh_stories", public_id=None):
        """Upload an image file to Cloudinary."""
        try:
            result = cloudinary.uploader.upload(
                file_path,
                folder=folder,
                public_id=public_id,
                resource_type="image"
            )
            return {
                "url": result.get("secure_url"),
                "public_id": result.get("public_id"),
                "format": result.get("format"),
            }
        except Exception as e:
            logger.error(f"Cloudinary upload error: {e}")
            raise Exception(f"Image upload failed: {str(e)}")

    def upload_url(self, image_url, folder="vansh_stories"):
        """Upload an image from a URL (e.g., DALL-E 3) to Cloudinary."""
        try:
            result = cloudinary.uploader.upload(
                image_url,
                folder=folder,
                resource_type="image"
            )
            return {
                "url": result.get("secure_url"),
                "public_id": result.get("public_id"),
            }
        except Exception as e:
            logger.error(f"Cloudinary URL upload error: {e}")
            raise Exception(f"Image upload from URL failed: {str(e)}")

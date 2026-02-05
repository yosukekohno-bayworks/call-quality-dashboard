import uuid
from datetime import datetime, timedelta
from pathlib import Path

from google.cloud import storage
from google.cloud.exceptions import NotFound

from app.config import settings


class StorageService:
    """Google Cloud Storage service for audio file management."""

    def __init__(self):
        self._client: storage.Client | None = None
        self._bucket: storage.Bucket | None = None

    @property
    def client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client(project=settings.GCS_PROJECT_ID)
        return self._client

    @property
    def bucket(self) -> storage.Bucket:
        if self._bucket is None:
            self._bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
        return self._bucket

    def _generate_blob_path(
        self,
        tenant_id: str,
        filename: str,
        prefix: str = "audio",
    ) -> str:
        """Generate a unique blob path for the file."""
        date_str = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = uuid.uuid4().hex[:8]
        extension = Path(filename).suffix
        safe_filename = f"{unique_id}{extension}"
        return f"{prefix}/{tenant_id}/{date_str}/{safe_filename}"

    async def upload_audio_file(
        self,
        file_content: bytes,
        filename: str,
        tenant_id: str,
        content_type: str = "audio/mpeg",
        ttl_days: int = 7,
    ) -> dict:
        """
        Upload an audio file to GCS with TTL metadata.

        Args:
            file_content: The file content as bytes
            filename: Original filename
            tenant_id: Tenant ID for organizing files
            content_type: MIME type of the file
            ttl_days: Number of days before automatic deletion

        Returns:
            dict with blob_path, public_url, and signed_url
        """
        blob_path = self._generate_blob_path(tenant_id, filename)
        blob = self.bucket.blob(blob_path)

        # Set metadata including TTL expiration
        expiration_date = datetime.utcnow() + timedelta(days=ttl_days)
        blob.metadata = {
            "tenant_id": tenant_id,
            "original_filename": filename,
            "uploaded_at": datetime.utcnow().isoformat(),
            "expires_at": expiration_date.isoformat(),
            "ttl_days": str(ttl_days),
        }

        # Upload the file
        blob.upload_from_string(file_content, content_type=content_type)

        # Generate signed URL for temporary access
        signed_url = self.generate_signed_url(blob_path)

        return {
            "blob_path": blob_path,
            "gcs_uri": f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}",
            "signed_url": signed_url,
            "expires_at": expiration_date.isoformat(),
        }

    def generate_signed_url(
        self,
        blob_path: str,
        expiration_minutes: int = 60,
        method: str = "GET",
    ) -> str:
        """
        Generate a signed URL for temporary access to a file.

        Args:
            blob_path: The path to the blob in GCS
            expiration_minutes: URL validity period in minutes
            method: HTTP method (GET, PUT, etc.)

        Returns:
            Signed URL string
        """
        blob = self.bucket.blob(blob_path)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method=method,
        )
        return url

    async def download_file(self, blob_path: str) -> bytes:
        """
        Download a file from GCS.

        Args:
            blob_path: The path to the blob in GCS

        Returns:
            File content as bytes
        """
        blob = self.bucket.blob(blob_path)
        return blob.download_as_bytes()

    async def delete_file(self, blob_path: str) -> bool:
        """
        Delete a file from GCS.

        Args:
            blob_path: The path to the blob in GCS

        Returns:
            True if deleted, False if not found
        """
        try:
            blob = self.bucket.blob(blob_path)
            blob.delete()
            return True
        except NotFound:
            return False

    async def file_exists(self, blob_path: str) -> bool:
        """Check if a file exists in GCS."""
        blob = self.bucket.blob(blob_path)
        return blob.exists()

    async def cleanup_expired_files(self, prefix: str = "audio/") -> int:
        """
        Delete files that have passed their TTL expiration.

        This should be called by a scheduled task (e.g., Cloud Scheduler).

        Args:
            prefix: Blob prefix to scan

        Returns:
            Number of deleted files
        """
        deleted_count = 0
        now = datetime.utcnow()

        blobs = self.client.list_blobs(self.bucket, prefix=prefix)
        for blob in blobs:
            if blob.metadata and "expires_at" in blob.metadata:
                expires_at = datetime.fromisoformat(blob.metadata["expires_at"])
                if now > expires_at:
                    blob.delete()
                    deleted_count += 1

        return deleted_count

    async def list_tenant_files(
        self,
        tenant_id: str,
        prefix: str = "audio",
        max_results: int = 100,
    ) -> list[dict]:
        """
        List files for a specific tenant.

        Args:
            tenant_id: Tenant ID
            prefix: Blob prefix
            max_results: Maximum number of results

        Returns:
            List of file metadata dicts
        """
        full_prefix = f"{prefix}/{tenant_id}/"
        blobs = self.client.list_blobs(
            self.bucket,
            prefix=full_prefix,
            max_results=max_results,
        )

        files = []
        for blob in blobs:
            files.append({
                "blob_path": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created_at": blob.time_created.isoformat() if blob.time_created else None,
                "metadata": blob.metadata,
            })

        return files


# Singleton instance
storage_service = StorageService()


def get_storage_service() -> StorageService:
    return storage_service

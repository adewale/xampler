"""Compatibility shim for the R2 example.

The stable R2 API now lives in ``xampler.r2``. This module remains so older
example-local imports and tutorials continue to work during the migration.
"""

from xampler.r2 import (
    ChecksumAlgorithm,
    MetadataField,
    R2Bucket,
    R2Conditional,
    R2HttpMetadata,
    R2ListResult,
    R2MultipartUpload,
    R2Object,
    R2ObjectInfo,
    R2ObjectRef,
    R2Range,
    R2UploadedPart,
    StorageClass,
    object_info,
)

__all__ = [
    "ChecksumAlgorithm",
    "MetadataField",
    "R2Bucket",
    "R2Conditional",
    "R2HttpMetadata",
    "R2ListResult",
    "R2MultipartUpload",
    "R2Object",
    "R2ObjectInfo",
    "R2ObjectRef",
    "R2Range",
    "R2UploadedPart",
    "StorageClass",
    "object_info",
]

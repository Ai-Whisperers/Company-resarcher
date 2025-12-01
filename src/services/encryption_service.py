"""
Encryption service for secure data storage.

Provides:
- Fernet symmetric encryption for vault data
- Key management with rotation support
- Encrypted file I/O operations
- Access control logging

Usage:
    from src.services.encryption_service import get_encryption_service

    service = get_encryption_service()
    encrypted = service.encrypt(data)
    decrypted = service.decrypt(encrypted)
"""

import base64
import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from ..core.logger import setup_logger


logger = setup_logger("encryption")


# Try to import cryptography, gracefully degrade if not available
try:
    from cryptography.fernet import Fernet, InvalidToken, MultiFernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception
    MultiFernet = None
    logger.warning(
        "cryptography package not installed. Encryption features disabled. "
        "Install with: pip install cryptography"
    )


@dataclass
class EncryptionKey:
    """Represents an encryption key with metadata."""
    key_id: str
    key_bytes: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_primary: bool = False

    @property
    def is_expired(self) -> bool:
        """Check if the key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class EncryptedData:
    """Container for encrypted data with metadata."""
    ciphertext: bytes
    key_id: str
    encrypted_at: datetime
    algorithm: str = "fernet"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ciphertext": base64.b64encode(self.ciphertext).decode("utf-8"),
            "key_id": self.key_id,
            "encrypted_at": self.encrypted_at.isoformat(),
            "algorithm": self.algorithm,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EncryptedData":
        """Create from dictionary."""
        return cls(
            ciphertext=base64.b64decode(data["ciphertext"]),
            key_id=data["key_id"],
            encrypted_at=datetime.fromisoformat(data["encrypted_at"]),
            algorithm=data.get("algorithm", "fernet"),
        )


class KeyManager:
    """
    Manages encryption keys with rotation support.

    Keys can be:
    - Generated randomly
    - Derived from a master password using PBKDF2
    - Loaded from environment variables
    """

    KEY_ENV_VAR = "VAULT_ENCRYPTION_KEY"
    MASTER_PASSWORD_ENV_VAR = "VAULT_MASTER_PASSWORD"
    KEY_FILE_NAME = ".vault_key"

    def __init__(self, key_dir: Path = None):
        self._keys: Dict[str, EncryptionKey] = {}
        self._primary_key_id: Optional[str] = None
        self._key_dir = key_dir or Path.cwd()

    def initialize(self) -> bool:
        """
        Initialize key manager with available keys.

        Priority:
        1. Environment variable (VAULT_ENCRYPTION_KEY)
        2. Derived from master password (VAULT_MASTER_PASSWORD)
        3. Key file in key_dir
        4. Generate new key (development only)

        Returns:
            True if initialization successful
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("Cannot initialize key manager: cryptography not available")
            return False

        # Try environment variable first
        env_key = os.getenv(self.KEY_ENV_VAR)
        if env_key:
            try:
                key_bytes = base64.urlsafe_b64decode(env_key.encode())
                self._add_key(key_bytes, source="environment")
                logger.info("Loaded encryption key from environment variable")
                return True
            except Exception as e:
                logger.error(f"Invalid encryption key in environment: {e}")

        # Try master password derivation
        master_password = os.getenv(self.MASTER_PASSWORD_ENV_VAR)
        if master_password:
            try:
                key_bytes = self._derive_key_from_password(master_password)
                self._add_key(key_bytes, source="derived")
                logger.info("Derived encryption key from master password")
                return True
            except Exception as e:
                logger.error(f"Failed to derive key from master password: {e}")

        # Try key file
        key_file = self._key_dir / self.KEY_FILE_NAME
        if key_file.exists():
            try:
                key_data = json.loads(key_file.read_text())
                key_bytes = base64.urlsafe_b64decode(key_data["key"])
                self._add_key(key_bytes, source="file")
                logger.info(f"Loaded encryption key from file: {key_file}")
                return True
            except Exception as e:
                logger.error(f"Failed to load key from file: {e}")

        # Development mode: generate new key
        if os.getenv("ENVIRONMENT", "development").lower() == "development":
            logger.warning("No encryption key found - generating new key (DEVELOPMENT ONLY)")
            key_bytes = Fernet.generate_key()
            self._add_key(key_bytes, source="generated")

            # Save to file for persistence
            try:
                key_file.write_text(json.dumps({
                    "key": base64.urlsafe_b64encode(key_bytes).decode(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "warning": "DO NOT use in production. Set VAULT_ENCRYPTION_KEY instead.",
                }))
                logger.info(f"Saved generated key to: {key_file}")
            except Exception as e:
                logger.warning(f"Could not save generated key: {e}")

            return True

        logger.error(
            "No encryption key available. Set VAULT_ENCRYPTION_KEY or "
            "VAULT_MASTER_PASSWORD environment variable."
        )
        return False

    def _derive_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Derive an encryption key from a password using PBKDF2."""
        if salt is None:
            # Use a deterministic salt based on app identifier
            # This allows the same password to produce the same key
            salt = hashlib.sha256(b"company-researcher-vault-v1").digest()[:16]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended minimum for PBKDF2-SHA256
        )
        key_bytes = kdf.derive(password.encode())
        return base64.urlsafe_b64encode(key_bytes)

    def _add_key(self, key_bytes: bytes, source: str = "unknown") -> str:
        """Add a key to the manager and return its ID."""
        key_id = hashlib.sha256(key_bytes).hexdigest()[:16]

        self._keys[key_id] = EncryptionKey(
            key_id=key_id,
            key_bytes=key_bytes,
            created_at=datetime.now(timezone.utc),
            is_primary=len(self._keys) == 0,  # First key is primary
        )

        if self._primary_key_id is None:
            self._primary_key_id = key_id

        logger.debug(f"Added encryption key {key_id[:8]}... from {source}")
        return key_id

    def get_primary_key(self) -> Optional[EncryptionKey]:
        """Get the primary encryption key."""
        if self._primary_key_id:
            return self._keys.get(self._primary_key_id)
        return None

    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get a key by ID."""
        return self._keys.get(key_id)

    def rotate_key(self) -> Optional[str]:
        """
        Generate a new primary key for rotation.
        Old keys are kept for decryption of existing data.

        Returns:
            New key ID or None if rotation failed
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            return None

        try:
            # Mark old primary as non-primary
            if self._primary_key_id and self._primary_key_id in self._keys:
                self._keys[self._primary_key_id].is_primary = False

            # Generate new key
            new_key_bytes = Fernet.generate_key()
            new_key_id = self._add_key(new_key_bytes, source="rotation")

            # Update primary
            self._keys[new_key_id].is_primary = True
            self._primary_key_id = new_key_id

            logger.info(f"Rotated encryption key to: {new_key_id[:8]}...")
            return new_key_id

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return None


class EncryptionService:
    """
    High-level encryption service for vault data.

    Provides:
    - Transparent encryption/decryption of data
    - Support for key rotation with MultiFernet
    - Encrypted file operations
    - Access logging for audit
    """

    def __init__(self, key_manager: KeyManager = None):
        self.key_manager = key_manager or KeyManager()
        self._fernet: Optional[Fernet] = None
        self._multi_fernet: Optional[MultiFernet] = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the encryption service."""
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Encryption service disabled: cryptography not available")
            return False

        if not self.key_manager.initialize():
            return False

        # Create Fernet instance with primary key
        primary_key = self.key_manager.get_primary_key()
        if not primary_key:
            logger.error("No primary key available")
            return False

        try:
            self._fernet = Fernet(primary_key.key_bytes)

            # Create MultiFernet with all keys for decryption
            all_keys = [
                Fernet(k.key_bytes)
                for k in self.key_manager._keys.values()
            ]
            self._multi_fernet = MultiFernet(all_keys)

            self._initialized = True
            logger.info("Encryption service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Fernet: {e}")
            return False

    @property
    def is_available(self) -> bool:
        """Check if encryption is available."""
        return CRYPTOGRAPHY_AVAILABLE and self._initialized

    def encrypt(self, data: Union[str, bytes, dict]) -> Optional[EncryptedData]:
        """
        Encrypt data using the primary key.

        Args:
            data: String, bytes, or dict to encrypt

        Returns:
            EncryptedData container or None if encryption failed
        """
        if not self.is_available:
            logger.warning("Encryption not available - returning None")
            return None

        try:
            # Convert data to bytes
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode("utf-8")
            elif isinstance(data, str):
                data_bytes = data.encode("utf-8")
            else:
                data_bytes = data

            # Encrypt
            ciphertext = self._fernet.encrypt(data_bytes)

            primary_key = self.key_manager.get_primary_key()

            return EncryptedData(
                ciphertext=ciphertext,
                key_id=primary_key.key_id,
                encrypted_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None

    def decrypt(self, encrypted: Union[EncryptedData, bytes]) -> Optional[bytes]:
        """
        Decrypt data using any available key.

        Args:
            encrypted: EncryptedData container or raw ciphertext bytes

        Returns:
            Decrypted bytes or None if decryption failed
        """
        if not self.is_available:
            logger.warning("Encryption not available - returning None")
            return None

        try:
            if isinstance(encrypted, EncryptedData):
                ciphertext = encrypted.ciphertext
            else:
                ciphertext = encrypted

            # Use MultiFernet to try all keys
            return self._multi_fernet.decrypt(ciphertext)

        except InvalidToken:
            logger.error("Decryption failed: invalid token or key")
            return None
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def decrypt_to_string(self, encrypted: Union[EncryptedData, bytes]) -> Optional[str]:
        """Decrypt and return as string."""
        data = self.decrypt(encrypted)
        if data:
            return data.decode("utf-8")
        return None

    def decrypt_to_dict(self, encrypted: Union[EncryptedData, bytes]) -> Optional[dict]:
        """Decrypt and return as dictionary."""
        data = self.decrypt_to_string(encrypted)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                logger.error("Decrypted data is not valid JSON")
        return None

    def encrypt_file(self, file_path: Path, output_path: Path = None) -> bool:
        """
        Encrypt a file in place or to a new location.

        Args:
            file_path: Path to file to encrypt
            output_path: Optional output path (defaults to file_path + .enc)

        Returns:
            True if successful
        """
        if not self.is_available:
            return False

        try:
            # Read file
            data = file_path.read_bytes()

            # Encrypt
            encrypted = self.encrypt(data)
            if not encrypted:
                return False

            # Write encrypted file
            output = output_path or file_path.with_suffix(file_path.suffix + ".enc")
            output.write_text(json.dumps(encrypted.to_dict()))

            logger.info(f"Encrypted file: {file_path} -> {output}")
            return True

        except Exception as e:
            logger.error(f"Failed to encrypt file {file_path}: {e}")
            return False

    def decrypt_file(self, file_path: Path, output_path: Path = None) -> bool:
        """
        Decrypt a file.

        Args:
            file_path: Path to encrypted file
            output_path: Optional output path (removes .enc suffix by default)

        Returns:
            True if successful
        """
        if not self.is_available:
            return False

        try:
            # Read encrypted file
            encrypted_data = json.loads(file_path.read_text())
            encrypted = EncryptedData.from_dict(encrypted_data)

            # Decrypt
            data = self.decrypt(encrypted)
            if data is None:
                return False

            # Write decrypted file
            if output_path is None:
                if file_path.suffix == ".enc":
                    output_path = file_path.with_suffix("")
                else:
                    output_path = file_path.with_suffix(".dec")

            output_path.write_bytes(data)

            logger.info(f"Decrypted file: {file_path} -> {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to decrypt file {file_path}: {e}")
            return False

    def encrypt_vault_data(self, data: dict) -> Optional[str]:
        """
        Encrypt vault data and return as base64 string.

        This is the main method for encrypting vault entries.
        """
        encrypted = self.encrypt(data)
        if encrypted:
            return json.dumps(encrypted.to_dict())
        return None

    def decrypt_vault_data(self, encrypted_str: str) -> Optional[dict]:
        """
        Decrypt vault data from base64 string.

        This is the main method for decrypting vault entries.
        """
        try:
            encrypted_data = json.loads(encrypted_str)
            encrypted = EncryptedData.from_dict(encrypted_data)
            return self.decrypt_to_dict(encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt vault data: {e}")
            return None

    def rotate_keys(self) -> bool:
        """
        Rotate encryption keys.

        After rotation, new encryptions use the new key,
        but old data can still be decrypted.

        Returns:
            True if rotation successful
        """
        if not self.is_available:
            return False

        new_key_id = self.key_manager.rotate_key()
        if not new_key_id:
            return False

        # Reinitialize with new keys
        return self.initialize()


# Module-level singleton
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get the global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
        _encryption_service.initialize()
    return _encryption_service


def is_encryption_available() -> bool:
    """Check if encryption is available."""
    return CRYPTOGRAPHY_AVAILABLE


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Classes
    "EncryptionService",
    "KeyManager",
    "EncryptionKey",
    "EncryptedData",
    # Functions
    "get_encryption_service",
    "is_encryption_available",
    # Constants
    "CRYPTOGRAPHY_AVAILABLE",
]

"""
Cryptography Utilities
Encryption, decryption, hashing, and key management
"""

import hashlib
import secrets
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import logging

logger = logging.getLogger(__name__)


class CryptoUtils:
    """
    Utility class for cryptographic operations
    """
    
    @staticmethod
    def generate_key(size: int = 32) -> bytes:
        """
        Generate a random cryptographic key
        
        Args:
            size: Key size in bytes (default: 32 for AES-256)
            
        Returns:
            Random key bytes
        """
        return secrets.token_bytes(size)
    
    @staticmethod
    def derive_key(password: str, salt: Optional[bytes] = None, iterations: int = 100000) -> Tuple[bytes, bytes]:
        """
        Derive a key from a password using PBKDF2
        
        Args:
            password: Password string
            salt: Salt bytes (generated if not provided)
            iterations: Number of PBKDF2 iterations
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key, salt
    
    @staticmethod
    def encrypt(data: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-256-GCM
        
        Args:
            data: Data to encrypt
            key: 32-byte encryption key
            
        Returns:
            Tuple of (ciphertext, nonce)
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        return ciphertext, nonce
    
    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM
        
        Args:
            ciphertext: Encrypted data
            key: 32-byte encryption key
            nonce: 12-byte nonce used during encryption
            
        Returns:
            Decrypted data
            
        Raises:
            ValueError: If decryption fails (wrong key or tampered data)
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - invalid key or tampered data")
    
    @staticmethod
    def encrypt_to_string(data: str, key: bytes) -> str:
        """
        Encrypt string data and return base64-encoded result
        
        Args:
            data: String to encrypt
            key: Encryption key
            
        Returns:
            Base64-encoded string containing nonce and ciphertext
        """
        ciphertext, nonce = CryptoUtils.encrypt(data.encode('utf-8'), key)
        # Combine nonce and ciphertext
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode('ascii')
    
    @staticmethod
    def decrypt_from_string(encrypted_data: str, key: bytes) -> str:
        """
        Decrypt base64-encoded encrypted string
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            key: Decryption key
            
        Returns:
            Decrypted string
        """
        combined = base64.b64decode(encrypted_data.encode('ascii'))
        nonce = combined[:12]
        ciphertext = combined[12:]
        plaintext = CryptoUtils.decrypt(ciphertext, key, nonce)
        return plaintext.decode('utf-8')


class HashUtils:
    """
    Utility class for hashing operations
    """
    
    @staticmethod
    def sha256(data: bytes) -> str:
        """
        Generate SHA-256 hash
        
        Args:
            data: Data to hash
            
        Returns:
            Hex-encoded hash string
        """
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def sha256_file(file_path: str, chunk_size: int = 8192) -> str:
        """
        Generate SHA-256 hash of a file
        
        Args:
            file_path: Path to file
            chunk_size: Size of chunks to read
            
        Returns:
            Hex-encoded hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def sha512(data: bytes) -> str:
        """
        Generate SHA-512 hash
        
        Args:
            data: Data to hash
            
        Returns:
            Hex-encoded hash string
        """
        return hashlib.sha512(data).hexdigest()
    
    @staticmethod
    def hash_with_algorithm(data: bytes, algorithm: str = "SHA256") -> str:
        """
        Generate hash using specified algorithm
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm (SHA256, SHA512, etc.)
            
        Returns:
            Hex-encoded hash string
        """
        algorithm = algorithm.upper()
        if algorithm == "SHA256":
            return HashUtils.sha256(data)
        elif algorithm == "SHA512":
            return HashUtils.sha512(data)
        elif algorithm == "SHA384":
            return hashlib.sha384(data).hexdigest()
        elif algorithm == "SHA224":
            return hashlib.sha224(data).hexdigest()
        elif algorithm == "SHA1":
            return hashlib.sha1(data).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    @staticmethod
    def hash_string(data: str, algorithm: str = "SHA256") -> str:
        """
        Hash a string
        
        Args:
            data: String to hash
            algorithm: Hash algorithm
            
        Returns:
            Hex-encoded hash string with algorithm prefix (e.g., "sha256:abc123...")
        """
        hash_value = HashUtils.hash_with_algorithm(data.encode('utf-8'), algorithm)
        return f"{algorithm.lower()}:{hash_value}"


class KeyManager:
    """
    Simple key management for encryption keys
    """
    
    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize key manager
        
        Args:
            master_key: Master encryption key (generated if not provided)
        """
        self.master_key = master_key or CryptoUtils.generate_key(32)
    
    def wrap_key(self, key_to_wrap: bytes) -> str:
        """
        Wrap (encrypt) a key with the master key
        
        Args:
            key_to_wrap: Key to encrypt
            
        Returns:
            Base64-encoded wrapped key
        """
        return CryptoUtils.encrypt_to_string(base64.b64encode(key_to_wrap).decode(), self.master_key)
    
    def unwrap_key(self, wrapped_key: str) -> bytes:
        """
        Unwrap (decrypt) a key
        
        Args:
            wrapped_key: Wrapped key string
            
        Returns:
            Original key bytes
        """
        unwrapped = CryptoUtils.decrypt_from_string(wrapped_key, self.master_key)
        return base64.b64decode(unwrapped)
    
    def generate_data_key(self) -> Tuple[bytes, str]:
        """
        Generate a new data encryption key and wrap it
        
        Returns:
            Tuple of (plaintext_key, wrapped_key)
        """
        plaintext_key = CryptoUtils.generate_key(32)
        wrapped_key = self.wrap_key(plaintext_key)
        return plaintext_key, wrapped_key


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token
    
    Args:
        length: Token length in bytes
        
    Returns:
        URL-safe base64-encoded token
    """
    return secrets.token_urlsafe(length)


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if equal, False otherwise
    """
    return secrets.compare_digest(a, b)

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os
from typing import Optional
from loguru import logger
from config import settings

class EncryptionService:
    """Service for encrypting sensitive data at rest."""
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            key: Encryption key (will generate if not provided)
        """
        if key:
            self.key = key.encode()
        else:
            # Generate a key if not provided
            self.key = Fernet.generate_key()
            logger.warning("Generated new encryption key. Save this for production use.")
        
        self.cipher = Fernet(self.key)
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt data.
        
        Args:
            data: Plain text to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted plain text
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None):
        """
        Encrypt a file.
        
        Args:
            file_path: Path to file to encrypt
            output_path: Path for encrypted output (defaults to file_path + .enc)
        """
        if not output_path:
            output_path = file_path + ".enc"
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted = self.cipher.encrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            logger.info(f"File encrypted: {file_path} -> {output_path}")
        except Exception as e:
            logger.error(f"File encryption error: {e}")
            raise
    
    def decrypt_file(self, encrypted_path: str, output_path: str):
        """
        Decrypt a file.
        
        Args:
            encrypted_path: Path to encrypted file
            output_path: Path for decrypted output
        """
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.cipher.decrypt(encrypted)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            logger.info(f"File decrypted: {encrypted_path} -> {output_path}")
        except Exception as e:
            logger.error(f"File decryption error: {e}")
            raise

# Initialize encryption service
encryption_key = settings.ENCRYPTION_KEY
if encryption_key:
    encryption_service = EncryptionService(encryption_key)
else:
    encryption_service = EncryptionService()
    logger.info(f"Generated encryption key: {encryption_service.key.decode()}")
    logger.info("Add this to your .env file as ENCRYPTION_KEY for production")

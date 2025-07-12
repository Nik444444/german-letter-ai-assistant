"""
Database models for user management
"""
import uuid
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

# MongoDB connection
mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/german_letters_db")
client = AsyncIOMotorClient(mongo_url)
database: AsyncIOMotorDatabase = client.german_letters_db

# Collections
users_collection = database.users

class UserApiKeys(BaseModel):
    """API keys for different LLM providers"""
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None

class UserRegistration(BaseModel):
    """User registration model"""
    email: EmailStr
    password: str
    name: str
    api_keys: Optional[UserApiKeys] = None  # Make API keys optional

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    """User profile model"""
    id: str
    email: str
    name: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class UserInDB(BaseModel):
    """User model as stored in database"""
    id: str
    email: str
    name: str
    password_hash: str
    api_keys: Dict[str, str]  # Encrypted API keys
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class ApiKeyUpdate(BaseModel):
    """Model for updating API keys"""
    api_keys: UserApiKeys

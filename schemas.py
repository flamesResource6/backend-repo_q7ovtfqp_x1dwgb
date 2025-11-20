"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Examsaathi auth/lead capture schema
class Auth(BaseModel):
    """
    Auth collection schema
    Collection name: "auth"
    Stores lightweight OTP flow state and basic profile fields.
    """
    name: str = Field(..., description="Full name")
    phone: str = Field(..., description="Phone number with country code or national format")
    otp_code: Optional[str] = Field(None, description="Latest OTP code (transient)")
    otp_expires: Optional[datetime] = Field(None, description="OTP expiration timestamp")
    verified: bool = Field(False, description="Whether phone was verified via OTP")

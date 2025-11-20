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
from typing import Optional, Literal

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

# Notion-like productivity app schemas

class Workspace(BaseModel):
    """
    Workspaces collection schema
    Collection name: "workspace"
    """
    name: str = Field(..., description="Workspace name")

class Page(BaseModel):
    """
    Pages collection schema
    Collection name: "page"
    """
    workspace_id: str = Field(..., description="Reference to workspace _id (string)")
    title: str = Field("Untitled", description="Page title")

class Block(BaseModel):
    """
    Blocks collection schema
    Collection name: "block"
    """
    page_id: str = Field(..., description="Reference to page _id (string)")
    type: Literal["text", "todo"] = Field("text", description="Block type")
    content: str = Field("", description="Block textual content")
    checked: Optional[bool] = Field(False, description="Todo checked state (for todo blocks)")
    position: int = Field(0, ge=0, description="Order position within the page")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!

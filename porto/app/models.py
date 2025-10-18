from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Request/Response Models
class LoginRequest(BaseModel):
    email: Optional[str] = None
    password: str
    identifier: Optional[str] = None


class User(BaseModel):
    id: str
    email: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: User


class Project(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    stack: List[str] = []
    featured: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Image(BaseModel):
    id: Optional[str] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    data_uri: Optional[str] = None
    created_at: Optional[datetime] = None


class Message(BaseModel):
    id: Optional[int] = None
    name: str
    email: Optional[str] = None
    message: str
    read: Optional[bool] = None
    created_at: Optional[datetime] = None


class Comment(BaseModel):
    id: Optional[int] = None
    author: Optional[str] = None
    message: str
    created_at: Optional[datetime] = None


class Experience(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    description: str
    start_date: str
    end_date: Optional[str] = None
    created_at: Optional[datetime] = None


class BlogPost(BaseModel):
    id: Optional[str] = None
    title: str
    slug: Optional[str] = None
    excerpt: str
    content: Optional[str] = None
    featured_image: Optional[str] = None
    tags: List[str] = []
    published: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Stats(BaseModel):
    projects: int = 0
    images: int = 0
    unread: int = 0
    experiences: int = 0
    comments: int = 0
    blog_posts: int = 0


class PaginatedResponse(BaseModel):
    items: List
    total: int

"""Pydantic models for the application."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """Base user model."""

    username: str = Field(..., min_length=3, max_length=50)
    first_name: str | None = Field(None, min_length=1, max_length=100)
    user_tg_id: int = Field(..., gt=0)


class UserCreate(UserBase):
    """User creation model."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("username")
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            error_message = "Username must be alphanumeric"
            raise ValueError(error_message)
        return v.lower()


class UserUpdate(BaseModel):
    """User update model."""

    username: str | None = Field(None, min_length=3, max_length=50)
    first_name: str | None = Field(None, min_length=1, max_length=100)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserInDB(UserBase):
    """User model for database representation."""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CartBase(BaseModel):
    """Base cart model."""

    name: str = Field(..., min_length=1, max_length=100)


class CartCreate(CartBase):
    """Cart creation model."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CartUpdate(BaseModel):
    """Cart update model."""

    name: str | None = Field(None, min_length=1, max_length=100)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CartInDB(CartBase):
    """Cart model for database representation."""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Base product model."""

    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(0.0, ge=0)


class ProductCreate(ProductBase):
    """Product creation model."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProductUpdate(BaseModel):
    """Product update model."""

    name: str | None = Field(None, min_length=1, max_length=200)
    price: float | None = Field(None, ge=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProductInDB(ProductBase):
    """Product model for database representation."""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

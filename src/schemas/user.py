from pydantic import BaseModel, UUID4, validator, Field
from datetime import datetime


class UserSchemaBase(BaseModel):
    username: str

    class Config:
        orm_mode = True


class UserSchemaCreate(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=8, max_length=32)


class UserSchemaUpdate(BaseModel):
    username: str | None = Field(min_length=2, max_length=20)
    password: str | None = Field(min_length=8, max_length=32)


class UserSchemaUpdateAvatar(BaseModel):
    avatar_id: UUID4 | None


class UserSchemaUpdateAdmin(UserSchemaUpdate):
    role_name: str | None = Field(min_length=2, max_length=20)


class UserSchema(BaseModel):
    id: UUID4
    username: str
    role: "RoleSchemaBase" = Field(exclude={"id"})
    created_at: str
    updated_at: str
    avatar: "ImageSchemaBase" = Field()

    @validator("created_at", "updated_at", pre=True)
    def parse_dates(cls, value):
        return datetime.strftime(value, "%X %d.%m.%Y %Z")

    class Config:
        orm_mode = True


from .role import RoleSchemaBase
from .image import ImageSchemaBase

UserSchema.update_forward_refs()

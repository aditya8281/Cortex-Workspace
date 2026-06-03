from pydantic import BaseModel, Field


class UserProfileSchema(BaseModel):
    display_name: str | None = None
    email: str | None = None
    job_title: str | None = None
    location: str | None = None
    bio: str | None = None
    interests: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    primary_languages: list[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    completion_percent: int = 0


class UserProfileUpdateSchema(BaseModel):
    display_name: str | None = None
    job_title: str | None = None
    location: str | None = None
    bio: str | None = None
    interests: list[str] | None = None
    goals: list[str] | None = None
    focus_areas: list[str] | None = None
    primary_languages: list[str] | None = None
    onboarding_completed: bool | None = None

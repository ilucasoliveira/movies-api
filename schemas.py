from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date
from models import MovieStatus

class SchemaGenre(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(min_length=2, max_length=50, description="Genre's type")
    
    @field_validator("name")
    @classmethod
    def name_to_lower(cls, value):
        result = value.strip().lower()
        return result

class SchemaGenreResponse(SchemaGenre):
    id: int

class SchemaMovie(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(min_length=2, max_length=100, description="Movie's title")
    year: int = Field(ge=1900, description="Its release")
    genres: list[str]
    rating: float | None = Field(default=None, ge=0, le=10, description="rating about the movie")
    status: MovieStatus = Field(default=MovieStatus.WANT_TO_WATCH, description="Movie's status")
    watched_at: date | None = Field(default=None, description= "watched movie's date")

class SchemaMovieResponse(SchemaMovie):
    id: int
    
    @field_validator("genres", mode="before")
    @classmethod
    def genres_to_name(cls, value):
        result = [genre.name for genre in value]
        return result

class SchemaMovieUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    title: str | None = Field(default=None, min_length=2, max_length=100)
    year: int | None = Field(default=None, ge=1900)
    genres: list[str] | None = Field(default=None)
    rating: float | None = Field(default=None, ge=0, le=10)
    status: MovieStatus | None = Field(default=None)
    watched_at: date | None = Field(default=None)
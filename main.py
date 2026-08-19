from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
from database import init_db, get_db
from auth import user_authenticate
from models import Genre, Movie
from schemas import SchemaGenre, SchemaGenreResponse, SchemaMovie, SchemaMovieResponse, SchemaMovieUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    lifespan=lifespan,
    title="Movie and TV Series Manager",
    description="A manager that organizes the movies and TV series you've watched.",
    version="1.0.0",
    contact={
        "name":"Lucas de Oliveira",
        "email":"lucasdeoliveira@gmail.com"
        }
)

@app.get("/")
async def health_check():
    return {"status": "OK"}

@app.post("/genres", status_code=201, response_model=SchemaGenreResponse)
async def create_genre(genre: SchemaGenre, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: AsyncSession = Depends(get_db)):
    
    new_genre = Genre(**genre.model_dump())
    
    try:
        db.add(new_genre)
        await db.commit()
        await db.refresh(new_genre)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This genre has already existed in database. Please, try again!")
    
    return new_genre

@app.get("/genres", status_code=200, response_model=list[SchemaGenreResponse])
async def read_genres(credentials: HTTPBasicCredentials = Depends(user_authenticate), db: AsyncSession = Depends(get_db)):
    
    result = await db.execute(select(Genre))
    genres = result.scalars().all()
    
    return genres

@app.post("/movies", status_code=201, response_model=SchemaMovieResponse)
async def create_movies(movie: SchemaMovie, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: AsyncSession = Depends(get_db)):
    
    genre_name = movie.genres
    new_movie = Movie(**movie.model_dump(exclude={"genres"}))
    
    result = await db.execute(select(Genre).where(Genre.name.in_(genre_name)))
    found_genres = result.scalars().all()
    found_genres_names = [genre.name for genre in found_genres]
    
    if set(movie.genres) != set(found_genres_names):
        left_names = set(movie.genres) - set(found_genres_names)
        raise HTTPException(status_code=400, detail=f"Genres not found: {', '.join(left_names)}")
    
    new_movie.genres = found_genres
    
    try:
        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie, ["genres"])
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This movie has already existed in database. Please, try again!")
    
    return new_movie

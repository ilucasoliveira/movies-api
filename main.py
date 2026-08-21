from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import user_authenticate
from cache import cache_save, cache_get, cache_delete
from database import get_db, init_db
from models import Genre, Movie
from schemas import (
    SchemaGenre,
    SchemaGenreResponse,
    SchemaMovie,
    SchemaMovieResponse,
    SchemaMovieUpdate,
)

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
        "email":"lucasdeoliveira937@gmail.com"
        }
)

def movie_key(id):
    return f"movie:{id}"

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
    
    await cache_delete("movies")
    
    return new_movie

@app.get("/movies", status_code=200, response_model=list[SchemaMovieResponse])
async def read_movies(credentials: HTTPBasicCredentials = Depends(user_authenticate), db: AsyncSession = Depends(get_db)):
    
    data_redis = await cache_get("movies")
    
    if data_redis is not None:
        return data_redis
    
    movies = await db.execute(select(Movie).options(selectinload(Movie.genres)))
    movies_result = movies.scalars().all()
    
    movies_to_cache = [SchemaMovieResponse.model_validate(movie).model_dump(mode="json") for movie in movies_result]
    
    await cache_save("movies", movies_to_cache)
    
    return movies_result

@app.get("/movies/{id}", status_code=200, response_model=SchemaMovieResponse)
async def read_one_movie(id: int, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: AsyncSession = Depends(get_db)):
    
    data_redis = await cache_get(movie_key(id))
    if data_redis is not None:
        return data_redis
    
    movie = await db.execute(select(Movie).filter(Movie.id == id).options(selectinload(Movie.genres)))
    result_movie = movie.scalars().first()
    
    if not result_movie:
        raise HTTPException(status_code=404, detail="Movie or tv show not found.")
    
    movie_to_cache = SchemaMovieResponse.model_validate(result_movie).model_dump(mode="json")
    
    await cache_save(movie_key(id), movie_to_cache) 
    
    return result_movie

@app.patch("/movies/{id}", status_code=200, response_model=SchemaMovieResponse)
async def update_movie(id: int, update_movie: SchemaMovieUpdate, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: AsyncSession = Depends(get_db)):
    
    movie = await db.execute(select(Movie).filter(Movie.id == id).options(selectinload(Movie.genres)))
    result_movie = movie.scalars().first()
    
    if not result_movie:
        raise HTTPException(status_code=404, detail="Movie or tv show not found.")
    
    update_data = update_movie.model_dump(exclude_unset=True)
    genres_names = update_data.pop("genres", None)
    
    if genres_names is not None:
        genres_data = await db.execute(select(Genre).where(Genre.name.in_(genres_names)))
        result_genres_data = genres_data.scalars().all()
        found_genres_names = [genre.name for genre in result_genres_data]
        
        if set(update_movie.genres) != set(found_genres_names):
            left_names = set(update_movie.genres) - set(found_genres_names)
            raise HTTPException(status_code=400, detail=f"Genres not found: {', '.join(left_names)}")
        
        result_movie.genres = result_genres_data
    
    for key, value in update_data.items():
        setattr(result_movie, key, value)
    
    try:
        await db.commit()
        await db.refresh(result_movie, ["genres"])
        await cache_delete("movies")
        await cache_delete(movie_key(id))
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This movie has already existed in database. Please, try again!")
    
    return result_movie

@app.delete("/movies/{id}", status_code=204)
async def delete_movie(id: int, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: AsyncSession = Depends(get_db)):
    
    movie = await db.execute(select(Movie).filter(Movie.id == id).options(selectinload(Movie.genres)))
    result_movie = movie.scalars().first()
    
    if not result_movie:
        raise HTTPException(status_code=404, detail="Movie or tv show not found.")
    
    await db.delete(result_movie)
    await db.commit()
    await cache_delete("movies")
    await cache_delete(movie_key(id))
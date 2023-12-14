from fastapi import APIRouter, Depends, status, Request

from sqlalchemy.orm import Session
from core.utils.search import es

from core.models.user import UserRole
from core.models.song import Song
from core.schemas.song import Song as SongSchema

from core.utils.dependencies import get_db
from core.utils.errors import handle_exception, not_found_error, unauthorized_error
from core.utils.middlewares import authenticate_common, authenticate_artist

router = APIRouter(
    prefix="/song",
    tags=["Song"],
)


@router.post(
    "/create",
    dependencies=[Depends(authenticate_artist)],
    status_code=status.HTTP_200_OK,
)
async def create_song(song: SongSchema, db: Session = Depends(get_db)):
    """
    Creates a new song.
    """

    new_song = Song(
        title=song.title,
        artist_id=song.artist_id,
        album_id=song.album_id,
        genre=song.genre,
        length=song.length,
    )

    try:
        db.add(new_song)
        db.commit()
        db.refresh(new_song)

        song_document = {
            "id": new_song.id,
            "title": new_song.title,
            "artist_id": new_song.artist_id,
            "album_id": new_song.album_id,
            "genre": new_song.genre,
            "length": new_song.length,
        }

        es.index(index="songs", id=new_song.id, body=song_document)

        return {"message": "Song Created Successfully!", "data": new_song}
    except Exception as e:
        raise handle_exception(e)


@router.get(
    "/{song_id}",
    dependencies=[Depends(authenticate_common)],
    status_code=status.HTTP_200_OK,
)
async def get_song(song_id: str, db: Session = Depends(get_db)):
    """
    Returns the song with the given id.
    """

    find_song = db.query(Song).filter(Song.id == song_id).first()

    if not find_song:
        raise not_found_error("Song")

    total_ratings = sum(rating.rating for rating in find_song.ratings)
    num_ratings = len(find_song.ratings) if find_song.ratings else 0
    average_rating = (total_ratings / num_ratings) if num_ratings != 0 else 0

    return {
        "message": "Song Found!",
        "data": {
            "id": find_song.id,
            "title": find_song.title,
            "artist": find_song.artist,
            "album": find_song.album,
            "genre": find_song.genre,
            "length": find_song.length,
            "ratings": {"total": num_ratings, "avg": average_rating},
        },
    }


@router.put(
    "/{song_id}",
    dependencies=[Depends(authenticate_artist)],
    status_code=status.HTTP_200_OK,
)
async def update_song(
    request: Request, song_id: str, song: SongSchema, db: Session = Depends(get_db)
):
    """
    Updates the song with the given id.
    """

    artist = request.state.user

    find_song = db.query(Song).filter(Song.id == song_id).first()

    if not find_song:
        raise not_found_error("Song")

    if find_song.artist_id != artist.id and artist.role != UserRole.ADMIN:
        raise unauthorized_error()

    try:
        find_song.title = song.title
        find_song.artist_id = song.artist_id
        find_song.album_id = song.album_id
        find_song.genre = song.genre
        find_song.length = song.length

        db.commit()
        db.refresh(find_song)

        song_document = {
            "id": find_song.id,
            "title": find_song.title,
            "artist_id": find_song.artist_id,
            "album_id": find_song.album_id,
            "genre": find_song.genre,
            "length": find_song.length,
        }

        es.update(index="songs", id=find_song.id, body={"doc": song_document})

        return {"message": "Song Updated Successfully!", "data": find_song}
    except Exception as e:
        raise handle_exception(e)


@router.delete(
    "/{song_id}",
    dependencies=[Depends(authenticate_artist)],
    status_code=status.HTTP_200_OK,
)
async def delete_song(request: Request, song_id: str, db: Session = Depends(get_db)):
    """
    Deletes the song with the given id.
    """

    artist = request.state.user

    find_song = db.query(Song).filter(Song.id == song_id).first()

    if not find_song:
        raise not_found_error("Song")

    if find_song.artist_id != artist.id and artist.role != UserRole.ADMIN:
        raise unauthorized_error()

    del_query = {"query": {"term": {"song_id": find_song.id}}}

    try:
        db.delete(find_song)
        db.commit()

        es.delete_by_query(index="ratings", body=del_query)
        es.delete(index="songs", id=find_song.id)

        return {"message": "Song Deleted Successfully!"}
    except Exception as e:
        raise handle_exception(e)
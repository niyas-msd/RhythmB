from fastapi import APIRouter, Depends, status, Request

from sqlalchemy.orm import Session

from core.models.playlist import Playlist
from core.models.song import Song

from core.schemas.playlist import Playlist as PlaylistSchema
from core.schemas.associations import SongPlaylistAssociation

from core.utils.dependencies import get_db
from core.utils.errors import handle_exception, not_found_error, unauthorized_error
from core.utils.middlewares import authenticate_common

router = APIRouter(
    prefix="/playlist",
    tags=["Playlist"],
)


@router.post(
    "/create",
    dependencies=[Depends(authenticate_common)],
    status_code=status.HTTP_200_OK,
)
async def create_playlist(
    request: Request, playlist: PlaylistSchema, db: Session = Depends(get_db)
):
    """
    Creates a new playlist.
    """

    user = request.state.user

    new_playlist = Playlist(title=playlist.title, user_id=user.id)

    try:
        db.add(new_playlist)
        db.commit()
        db.refresh(new_playlist)

        return {"message": "Playlist Created Successfully!", "data": new_playlist}
    except Exception as e:
        raise handle_exception(e)


@router.get(
    "/{playlist_id}",
    dependencies=[Depends(authenticate_common)],
    status_code=status.HTTP_200_OK,
)
async def get_playlist(playlist_id: str, db: Session = Depends(get_db)):
    """
    Returns the playlist with the given id.
    """

    find_playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not find_playlist:
        raise not_found_error("playlist")

    return {
        "message": "Playlist Found!",
        "data": {
            "playlist_id": find_playlist.id,
            "title": find_playlist.title,
            "songs": find_playlist.songs,
            "user": find_playlist.user.username,
        },
    }


@router.put(
    "/{playlist_id}",
    dependencies=[Depends(authenticate_common)],
    status_code=status.HTTP_200_OK,
)
async def update_playlist(
    request: Request,
    playlist_id: str,
    playlist: PlaylistSchema,
    db: Session = Depends(get_db),
):
    """
    Updates the playlist with the given id.
    """

    user = request.state.user

    find_playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not find_playlist:
        raise not_found_error("playlist")

    if find_playlist.user_id != user.id:
        raise unauthorized_error()

    try:
        find_playlist.title = playlist.title

        db.commit()
        db.refresh(find_playlist)

        return {"message": "Playlist Updated Successfully!", "data": find_playlist}
    except Exception as e:
        raise handle_exception(e)


@router.delete(
    "/{playlist_id}",
    dependencies=[Depends(authenticate_common)],
    status_code=status.HTTP_200_OK,
)
async def delete_playlist(
    request: Request, playlist_id: str, db: Session = Depends(get_db)
):
    """
    Deletes the playlist with the given id.
    """

    user = request.state.user

    find_playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()

    if not find_playlist:
        raise not_found_error("playlist")

    if find_playlist.user_id != user.id:
        raise unauthorized_error()

    try:
        db.delete(find_playlist)
        db.commit()

        return {"message": "Playlist Deleted Successfully!"}
    except Exception as e:
        raise handle_exception(e)


@router.post(
    "/add-song",
    dependencies=[Depends(authenticate_common)],
    status_code=status.HTTP_200_OK,
)
async def add_song_to_playlist(
    request: Request,
    association: SongPlaylistAssociation,
    db: Session = Depends(get_db),
):
    """
    Adds a song to the playlist with the given id.
    """

    user = request.state.user

    find_playlist = (
        db.query(Playlist).filter(Playlist.id == association.playlist_id).first()
    )

    if not find_playlist:
        raise not_found_error("playlist")

    if find_playlist.user_id != user.id:
        raise unauthorized_error()

    find_song = db.query(Song).filter(Song.id == association.song_id).first()

    if not find_song:
        raise not_found_error("song")

    if find_song in find_playlist.songs:
        return {
            "message": "Song Already Exists in Playlist!",
            "data": {
                "playlist_id": find_playlist.id,
                "title": find_playlist.title,
                "songs": find_playlist.songs,
                "user": find_playlist.user.username,
            },
        }

    try:
        find_playlist.songs.append(find_song)
        db.commit()
        db.refresh(find_playlist)

        return {
            "message": "Song Added to Playlist Successfully!",
            "data": {
                "playlist_id": find_playlist.id,
                "title": find_playlist.title,
                "songs": find_playlist.songs,
                "user": find_playlist.user.username,
            },
        }
    except Exception as e:
        raise handle_exception(e)


@router.post(
    "/remove-song",
    dependencies=[Depends(authenticate_common)],
    status_code=status.HTTP_200_OK,
)
async def remove_song_from_playlist(
    request: Request,
    association: SongPlaylistAssociation,
    db: Session = Depends(get_db),
):
    """
    Removes a song from the playlist with the given id.
    """

    user = request.state.user

    find_playlist = (
        db.query(Playlist).filter(Playlist.id == association.playlist_id).first()
    )

    if not find_playlist:
        raise not_found_error("playlist")

    if find_playlist.user_id != user.id:
        raise unauthorized_error()

    find_song = db.query(Song).filter(Song.id == association.song_id).first()

    if not find_song:
        raise not_found_error("song")

    if find_song not in find_playlist.songs:
        return {
            "message": "Song Does Not Exist in Playlist!",
            "data": {
                "playlist_id": find_playlist.id,
                "title": find_playlist.title,
                "songs": find_playlist.songs,
                "user": find_playlist.user.username,
            },
        }

    try:
        find_playlist.songs.remove(find_song)
        db.commit()
        db.refresh(find_playlist)

        return {
            "message": "Song Removed from Playlist Successfully!",
            "data": {
                "playlist_id": find_playlist.id,
                "title": find_playlist.title,
                "songs": find_playlist.songs,
                "user": find_playlist.user.username,
            },
        }
    except Exception as e:
        raise handle_exception(e)

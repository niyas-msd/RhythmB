import enum
from sqlalchemy import Enum, Column, Integer, String
from sqlalchemy.orm import relationship

from core.utils.database import Base


class UserRole(enum.Enum):
    ADMIN = "admin"
    ARTIST = "artist"
    COMMON = "common"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.COMMON)

    playlists = relationship("Playlist", back_populates="user")
    ratings = relationship("Rating", back_populates="user")

    def __repr__(self):
        return f"<User {self.username} {self.email}>"

from typing import Optional

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import (declarative_base, declared_attr, mapped_column,
                            Mapped, relationship)

Base = declarative_base()


class Photo(Base):
    __tablename__ = 'photos'
    id: Mapped[int] = mapped_column(primary_key=True)
    avito_url: Mapped[str] = mapped_column(unique=True)
    downloaded: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return f'ph. {self.id}'


class HasPhotos:
    '''Mixin for items with photos'''
    @declared_attr
    def photos(cls):
        photo_association = Table(
            f'{cls.__tablename__}_photos',
            cls.metadata,
            Column('photos_id', ForeignKey('photos.id'), primary_key=True),
            Column(
                f'{cls.__tablename__}_id',
                ForeignKey(f'{cls.__tablename__}.id'),
                primary_key=True,
            ),
        )
        return relationship(Photo, secondary=photo_association)


class Item(Base, HasPhotos):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)  # matches avito id
    price: Mapped[int]
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    available: Mapped[bool] = mapped_column(default=True)
    condition: Mapped[str] = mapped_column(String(32), nullable=True)

    def __repr__(self) -> str:
        return f'{self.name}'


class Garment(Item):
    __abstract__ = True
    size: Mapped[str] = mapped_column(String(32), nullable=True)
    brand: Mapped[str] = mapped_column(String(32), nullable=True)
    color: Mapped[str] = mapped_column(String(32), nullable=True)
    sex: Mapped[str] = mapped_column(String(16), nullable=True)
    tag: Mapped[str] = mapped_column(String(32), nullable=True)
    composition: Mapped[str] = mapped_column(String(64), nullable=True)


class AdultGarment(Garment):
    __tablename__ = 'adult_garments'


class ChildGarment(Garment):
    __tablename__ = 'child_garments'

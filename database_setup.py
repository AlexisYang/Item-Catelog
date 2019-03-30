import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.types import DateTime

Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Item(Base):
    __tablename__ = 'menu_item'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(350))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    time = Column(DateTime, nullable=False)

    @property
    def serialize(self):
        return {
            'cat_id': self.category_id,
            'description': self.description,
            'id': self.id,
            'title': self.name
        }


engine = create_engine('sqlite:///itemcatelog.db')


Base.metadata.create_all(engine)

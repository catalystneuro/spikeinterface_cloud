from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    datasets = relationship('Dataset', back_populates='user', cascade='all, delete-orphan')
    runs = relationship('Run', back_populates='user', cascade='all, delete-orphan')

    def update(self, key, value):
        setattr(self, key, value)


class Dataset(Base):
    __tablename__ = 'dataset'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='datasets')
    runs = relationship('Run', back_populates='dataset', cascade='all, delete-orphan')
    source = Column(Enum('dandi', 's3', 'local', name='source'))
    source_metadata = Column(String)

    def update(self, key, value):
        setattr(self, key, value)


class Run(Base):
    __tablename__ = 'run'
    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    description = Column(String)
    last_run = Column(String)
    status = Column(Enum('running', 'success', 'fail', name='status'))
    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    dataset = relationship('Dataset', back_populates='runs')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='runs')
    metadata_ = Column("metadata", String)

    def update(self, key, value):
        setattr(self, key, value)
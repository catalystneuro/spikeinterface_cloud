from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    data_sources = relationship('DataSource', back_populates='user', cascade='all, delete-orphan')
    runs = relationship('Run', back_populates='user', cascade='all, delete-orphan')

    def update(self, key, value):
        setattr(self, key, value)


class DataSource(Base):
    __tablename__ = 'data_source'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    source = Column(Enum('dandi', 's3', 'local', name='source'))
    source_data_type = Column(Enum('nwb', 'spikeglx', name='source_data_type'))
    source_data_urls = Column(String)
    recording_kwargs = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='data_sources')
    runs = relationship('Run', back_populates='data_source', cascade='all, delete-orphan')

    def update(self, key, value):
        setattr(self, key, value)


class Run(Base):
    __tablename__ = 'run'
    id = Column(Integer, primary_key=True)
    run_at = Column(Enum('local', 'aws', name='run_at'))
    identifier = Column(String)
    description = Column(String)
    last_run = Column(String)
    status = Column(Enum('running', 'success', 'fail', name='status'))
    data_source_id = Column(Integer, ForeignKey('data_source.id'))
    data_source = relationship('DataSource', back_populates='runs')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='runs')
    metadata_ = Column("metadata", String)
    logs = Column(String)
    output_path = Column(String)

    def update(self, key, value):
        setattr(self, key, value)
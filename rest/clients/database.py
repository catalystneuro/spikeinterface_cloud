from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import ast
import json

from ..db.models import User, DataSource, Run


class DatabaseClient:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        session = self.Session(expire_on_commit=False)
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def query_users(self):
        with self.session_scope() as session:
            return session.query(User).all()

    def user_exists(self, username):
        with self.session_scope() as session:
            return session.query(User).filter(User.username == username).count() > 0
        
    def query_runs(self):
        with self.session_scope() as session:
            return session.query(Run).all()

    def query_data_sources_by_user(self, user_id):
        with self.session_scope() as session:
            return session.query(DataSource).filter(DataSource.user_id == user_id).all()

    def query_runs_by_user(self, user_id):
        with self.session_scope() as session:
            return session.query(Run).filter(Run.user_id == user_id).all()

    def query_runs_by_data_source(self, data_source_id):
        with self.session_scope() as session:
            return session.query(Run).filter(Run.data_source_id == data_source_id).all()
        
    def query_run_by_id(self, run_id):
        with self.session_scope() as session:
            return session.query(Run).filter(Run.id == run_id).one_or_none()

    def create_user(self, username, password):
        user = User(username=username, password=password)
        with self.session_scope() as session:
            session.add(user)
            return user

    def create_data_source(self, name, description, user_id, source, source_data_type, source_data_paths, recording_kwargs):
        data_source = DataSource(
            name=name, 
            description=description, 
            user_id=user_id, 
            source=source, 
            source_data_type=source_data_type,
            source_data_paths=source_data_paths,
            recording_kwargs=recording_kwargs,
        )
        with self.session_scope() as session:
            session.add(data_source)
            return data_source

    def create_run(self, run_at, identifier, description, last_run, status, data_source_id, metadata, user_id, output_path, output_destination, logs=""):
        run = Run(
            run_at=run_at, 
            identifier=identifier, 
            description=description, 
            last_run=last_run, 
            status=status, 
            data_source_id=data_source_id, 
            user_id=user_id, 
            metadata_=metadata, 
            logs=logs,
            output_destination=output_destination,
            output_path=output_path,
        )
        with self.session_scope() as session:
            session.add(run)
            return run

    def get_user_info(self, username):
        with self.session_scope() as session:
            return session.query(User).filter(User.username == username).one_or_none()

    def get_data_source_info(self, data_source_id):
        with self.session_scope() as session:
            return session.query(DataSource).filter(DataSource.id == data_source_id).one_or_none()

    def get_run_info(self, run_id):
        with self.session_scope() as session:
            obj = session.query(Run).filter(Run.id == run_id).one_or_none()
            data_source = self.get_data_source_info(data_source_id=obj.data_source_id)
            return {
                "run_at": obj.run_at,
                "identifier": obj.identifier,
                "description": obj.description,
                "lastRun": obj.last_run,
                "status": obj.status,
                "dataSourceName": data_source.name,
                "metadata": json.loads(obj.metadata_),
                "logs": obj.logs,
                "outputPath": obj.output_path
            }
    
    def get_all_runs_info(self):
        with self.session_scope() as session:
            runs = session.query(Run).all()
            return [self.get_run_info(run_id=obj.id) for obj in runs]


    def update_user(self, user_id, key, value):
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).one_or_none()
            if user:
                user.update(key, value)
                session.add(user)
                return user
            return None
    

    def update_data_source(self, data_source_id, key, value):
        with self.session_scope() as session:
            data_source = session.query(DataSource).filter(DataSource.id == data_source_id).one_or_none()
            if data_source:
                data_source.update(key, value)
                session.add(data_source)
                return data_source
            return None
    

    def update_run(self, run_identifier, key, value):
        with self.session_scope() as session:
            run = session.query(Run).filter(Run.identifier == run_identifier).one_or_none()
            if run:
                run.update(key, value)
                session.add(run)
                return run
            return None
    

    def delete_run(self, run_identifier):
        with self.session_scope() as session:
            run = session.query(Run).filter(Run.identifier == run_identifier).one_or_none()
            if run:
                session.delete(run)
                return True
            return False
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import ast

from db.models import User, Dataset, Run


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

    def query_datasets_by_user(self, user_id):
        with self.session_scope() as session:
            return session.query(Dataset).filter(Dataset.user_id == user_id).all()

    def query_runs_by_user(self, user_id):
        with self.session_scope() as session:
            return session.query(Run).filter(Run.user_id == user_id).all()

    def query_runs_by_dataset(self, dataset_id):
        with self.session_scope() as session:
            return session.query(Run).filter(Run.dataset_id == dataset_id).all()
        
    def query_run_by_id(self, run_id):
        with self.session_scope() as session:
            return session.query(Run).filter(Run.id == run_id).one_or_none()

    def create_user(self, username, password):
        user = User(username=username, password=password)
        with self.session_scope() as session:
            session.add(user)
            return user

    def create_dataset(self, name, description, user_id, source, source_metadata):
        dataset = Dataset(name=name, description=description, user_id=user_id, source=source, source_metadata=source_metadata)
        with self.session_scope() as session:
            session.add(dataset)
            return dataset

    def create_run(self, run_at, identifier, description, last_run, status, dataset_id, metadata, user_id):
        run = Run(run_at=run_at, identifier=identifier, description=description, last_run=last_run, status=status, dataset_id=dataset_id, metadata_=metadata, user_id=user_id)
        with self.session_scope() as session:
            session.add(run)
            return run

    def get_user_info(self, username):
        with self.session_scope() as session:
            return session.query(User).filter(User.username == username).one_or_none()

    def get_dataset_info(self, dataset_id):
        with self.session_scope() as session:
            return session.query(Dataset).filter(Dataset.id == dataset_id).one_or_none()

    def get_run_info(self, run_id):
        with self.session_scope() as session:
            obj = session.query(Run).filter(Run.id == run_id).one_or_none()
            dataset = self.get_dataset_info(dataset_id=obj.dataset_id)
            return {
                "run_at": obj.run_at,
                "identifier": obj.identifier,
                "description": obj.description,
                "lastRun": obj.last_run,
                "status": obj.status,
                "datasetName": dataset.name,
                "metadata": ast.literal_eval(obj.metadata_),
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
    

    def update_dataset(self, dataset_id, key, value):
        with self.session_scope() as session:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).one_or_none()
            if dataset:
                dataset.update(key, value)
                session.add(dataset)
                return dataset
            return None
    

    def update_run(self, run_identifier, key, value):
        with self.session_scope() as session:
            dataset = session.query(Run).filter(Run.identifier == run_identifier).one_or_none()
            if dataset:
                dataset.update(key, value)
                session.add(dataset)
                return dataset
            return None
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from db.models import Base, User, Dataset, Run


def initialize_db(db: str):
    engine = create_engine(db)
    existing_tables = inspect(engine).get_table_names()

    print("############  existing tables  ############")
    print(existing_tables)

    clear_db = False
    if 'user' in existing_tables and clear_db:
        print("Clearing tables...")
        run_clear_db(db)

    # Check if the user table exists
    if 'user' not in existing_tables:
        # Create table schema
        print("Create new tables...")
        Base.metadata.create_all(engine)
        existing_tables = inspect(engine).get_table_names()
        print(existing_tables)
        # meta.create_all(engine)

        # Create a session and add the admin user to the database
        print("Will create new User - name: admin, password: admin")
        admin_user = User(username='admin', password='admin')
        Session = sessionmaker(bind=engine)
        with Session.begin() as session:
            session.add(admin_user)


def run_clear_db(db: str):
    # Check if the user table exists
    engine = create_engine(db)
    Run.__table__.drop(engine)
    Dataset.__table__.drop(engine)
    User.__table__.drop(engine)
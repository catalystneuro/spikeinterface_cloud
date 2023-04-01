from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from db.models import Base, User


def initialize_db(db: str):
    # Check if the user table exists
    engine = create_engine(db)
    existing_tables = inspect(engine).get_table_names()

    print("############  existing tables  ############")
    print(existing_tables)

    if 'user' not in existing_tables:
        print("Will create new User - name: admin, password: admin")
        # Create table schema
        Base.metadata.create_all(engine)

        # Add admin user
        admin_user = User(username='admin', password='admin')

        # Create a session and add the admin user to the database
        Session = sessionmaker(bind=engine)
        with Session.begin() as session:
            session.add(admin_user)
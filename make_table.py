"""
Database table and user creation script.
This script creates a basic table for storing scraped job items, and a user to manage it. Once
the script is executed items can be inserted, deleted, etc from the created table, with the new
user.

To use simply call the script with three arguments:

    -c | --credentials  the connection string to the PostgreSQL database instance for example:
                        "postgresql://user:pass@host:port/database". The username and password
                        should be those of a user with the CREATETABLE and CREATEROLE roles.
    -u | --username     the username of the to-be-created user.
    -p | --password     the password of the to-be-created user.

"""

import argparse
from contextlib import contextmanager

from sqlalchemy import Column, Text, create_engine, event
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class ScrapedJob(Base):
    __tablename__ = 'scraped-jobs'
    id = Column(UUID, server_default=func.gen_random_uuid())
    url = Column(Text, nullable=False, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    last_modified = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    data = Column(JSONB, nullable=False)

    def __repr__(self):
        return '<Job created_at: {self.created_at}' \
               ' last_modified: {self.last_modified}' \
               ' url: {self.url!r}' \
               '>'.format(self=self)


@event.listens_for(ScrapedJob, 'before_update', propagate=True)
def update_last_modified_timestamp(mapper, connection, row):
    # updates the value of the `last_modified` column when we're doing an UPDATE
    row.last_modified = func.now()


@contextmanager
def session_scope(credentials):
    """Provide a transactional scope around a series of operations."""
    engine = create_engine(credentials)
    session = sessionmaker(bind=engine)()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def install_pgcrypto(db_connection):
    db_connection.execute("""CREATE EXTENSION IF NOT EXISTS pgcrypto;""")


def create_table(db_connection):
    Base.metadata.create_all(db_connection, checkfirst=True)


def create_user(username, password, db_connection):
    query = """CREATE USER {user} WITH PASSWORD {password!r} NOINHERIT;""".format(user=username, password=password)
    db_connection.execute(query)


def alter_table_owner(username, table, db_session):
    query = """ALTER TABLE "{table}" OWNER TO {user};""".format(table=table, user=username)
    db_session.execute(query)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Database table and user tools')
    parser.add_argument('-c', '--credentials', dest='credentials')
    parser.add_argument('-u', '--username', dest='username')
    parser.add_argument('-p', '--password', dest='password')
    arguments = parser.parse_args()

    with session_scope(arguments.credentials) as session:
        connection = session.bind

        install_pgcrypto(connection)
        create_table(connection)
        create_user(arguments.username, arguments.password, connection)
        alter_table_owner(arguments.username, ScrapedJob.__tablename__, connection)

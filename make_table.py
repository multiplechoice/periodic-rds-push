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
import datetime

from sqlalchemy import Column, Text, DateTime, create_engine
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class JobsTable(Base):
    __tablename__ = 'scraped-jobs'
    id = Column(UUID, server_default=func.gen_random_uuid(), primary_key=True)
    url = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_modified = Column(DateTime, nullable=False)
    data = Column(JSONB, nullable=False)


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

    engine = create_engine(arguments.credentials, echo=True)
    session = sessionmaker(bind=engine)()
    connection = session.bind

    install_pgcrypto(connection)
    create_table(connection)
    create_user(arguments.username, arguments.password, connection)
    alter_table_owner(arguments.username, JobsTable.__tablename__, connection)

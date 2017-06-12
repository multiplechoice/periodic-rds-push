import argparse
import datetime

from sqlalchemy import Column, Text, DateTime, create_engine
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class JobsTable(Base):
    __tablename__ = 'jobs'
    id = Column(UUID, server_default=func.gen_random_uuid(), primary_key=True)
    url = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_modified = Column(DateTime, nullable=False)
    data = Column(JSONB, nullable=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Table maker thing!')
    parser.add_argument('-c', '--credentials', dest='credentials')
    arguments = parser.parse_args()

    engine = create_engine(arguments.credentials)
    session = sessionmaker(bind=engine)()
    # we need to install the pgcrypto extension to make use of the `gen_random_uuid` function
    session.bind.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto;')
    Base.metadata.create_all(session.bind, checkfirst=True)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
db_password = os.getenv("DB_PASSWORD")

engine = create_engine(f"postgresql+psycopg://postgres:{db_password}@localhost:5433/postgres",
                       echo=True)

Session = sessionmaker(engine)


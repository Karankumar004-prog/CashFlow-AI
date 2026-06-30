import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "cashflow_memory.db")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserMemoryOverride(Base):
    __tablename__ = "user_memory_overrides"

    id = Column(Integer, primary_key=True, index=True)
    clean_desc = Column(String, unique=True, index=True, nullable=False)
    merchant_name = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    sub_category = Column(String, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)

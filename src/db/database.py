from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/song_agent")
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    artist = Column(String(255))
    file_path = Column(String(512))
    hashes = relationship("Fingerprint", back_populates="song", cascade="all, delete-orphan")

class Fingerprint(Base):
    __tablename__ = "fingerprints"
    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    hash_value = Column(String(64), nullable=False, index=True) 
    offset = Column(Integer, nullable=False) 
    song = relationship("Song", back_populates="hashes")
    
    # 索引 查询
    __table_args__ = (Index("idx_hash", "hash_value"),)

def init_db():
    """初始化database 创建表"""
    Base.metadata.create_all(engine)

def get_db():
    """获取"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    appid = Column(Integer, nullable=False)
    market_hash_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    storage_uri = Column(String)  # s3://.../dataset.parquet
    sha256 = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    artifact_uri = Column(String)  # s3://.../model.pkl
    plot_uri = Column(String)      # s3://.../plot.png
    mse = Column(Float)
    r2 = Column(Float)
    status = Column(String)        # 'ready', 'training', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.database import Base

class WatchList(Base):
    __tablename__ = "watch_lists"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    ticker = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Signal(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker = Column(String, index=True, nullable=False)
    score = Column(Float)
    sentiment_label = Column(String)
    source_count = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sources = relationship("SignalSource", back_populates="signal", cascade="all, delete-orphan")

class SignalSource(Base):
    __tablename__ = "signal_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String)
    url = Column(String)
    snippet = Column(String)
    weight = Column(Float)

    signal = relationship("Signal", back_populates="sources")

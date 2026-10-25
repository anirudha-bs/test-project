import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Signal(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker = Column(String, index=True)
    score = Column(Float)
    sentiment_label = Column(String)
    source_count = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)

    sources = relationship("SignalSource", back_populates="signal")

class SignalSource(Base):
    __tablename__ = "signal_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String, ForeignKey("signals.id"))
    source_type = Column(String)
    url = Column(String)
    snippet = Column(Text)
    weight = Column(Float)

    signal = relationship("Signal", back_populates="sources")

class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    symbol = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

import datetime
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from engine.db.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    account_type = Column(String, nullable=False) # e.g. 'asset', 'liability'
    balance = Column(Float, default=0.0)
    
    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    date = Column(Date, nullable=False)
    raw_description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    
    # Enriched fields
    clean_merchant = Column(String, nullable=True)
    transaction_type = Column(String, nullable=True) # Income, Expense, Transfer, etc.
    category = Column(String, nullable=True)
    sub_category = Column(String, nullable=True)
    
    # Audit trail
    confidence_score = Column(Float, default=0.0)
    classification_method = Column(String, default="unclassified")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    account = relationship("Account", back_populates="transactions")

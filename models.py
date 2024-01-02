from sqlalchemy import Column, Integer, String, DateTime, func, Enum, UniqueConstraint, CheckConstraint, Float, \
    ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class StatusEnum(Enum):
    ACTIVE = 'ACTIVE'
    PASSIVE = 'PASSIVE'
    DELETED = 'DELETED'


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(length=255), unique=True, index=True, nullable=False)
    password = Column(String(length=255), nullable=False)
    date_created = Column(DateTime, server_default=func.now())
    date_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())
    cards = relationship('Card', back_populates='user')


class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(length=255))
    card_no = Column(String(length=255), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(length=255), CheckConstraint(f"status IN ('{StatusEnum.ACTIVE}', '{StatusEnum.PASSIVE}', '{StatusEnum.DELETED}')"), default=StatusEnum.PASSIVE)
    date_created = Column(DateTime, server_default=func.now())
    date_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user = relationship('User', back_populates='cards')
    transactions = relationship('Transaction', back_populates='card')

    # Unique constraint to prevent the same card number for the same user
    __table_args__ = (
        UniqueConstraint('card_no', 'user_id'),
    )


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    description = Column(String(length=255))
    card_id = Column(Integer, ForeignKey('cards.id'), nullable=False)
    date_created = Column(DateTime, server_default=func.now())
    date_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())
    card = relationship('Card', back_populates='transactions')

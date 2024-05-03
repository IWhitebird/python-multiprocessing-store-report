from typing import List
import enum , uuid , datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship ,DeclarativeBase , Mapped , mapped_column
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class Store(Base):
    __tablename__ = "Store"

    store_id : Mapped[str] = mapped_column(primary_key=True, nullable=False)
    timezone_str : Mapped[str] = mapped_column(nullable=False)
    statuses : Mapped[List["StoreStatus"]] = relationship(back_populates="store", cascade="all, delete-orphan")
    hours : Mapped[List["StoreHours"]] = relationship(back_populates="store", cascade="all, delete-orphan")

class StoreStatus(Base):
    __tablename__ = "StoreStatus"
    
    class Status(enum.Enum):
        ACTIVE = 'active'
        INACTIVE = 'inactive'
        
    store_id : Mapped[str] = mapped_column(ForeignKey('Store.store_id'), nullable=False)
    timestamp_utc : Mapped[datetime.datetime] = mapped_column(nullable=False)
    status : Mapped[Status] = mapped_column(nullable=False)
    store_status_id : Mapped[uuid.UUID] = mapped_column(primary_key=True, nullable=False, default=uuid.uuid4)
    store : Mapped["Store"] = relationship(back_populates="statuses")
    

class StoreHours(Base):
    __tablename__ = "StoreHours"
    
    store_id : Mapped[str] = mapped_column(ForeignKey('Store.store_id'), nullable=False)
    day_of_week : Mapped[int] = mapped_column(nullable=False)
    start_time_local : Mapped[datetime.time] = mapped_column(nullable=False)
    end_time_local : Mapped[datetime.time] = mapped_column(nullable=False)
    store_hour_id : Mapped[uuid.UUID] = mapped_column(primary_key=True, nullable=False, default=uuid.uuid4)
    store : Mapped["Store"] = relationship(back_populates="hours")


class StoreReport(Base):
    __tablename__ = "StoreReport"
    
    class PollingStatus(enum.Enum):
        PENDING = 'PENDING'
        SUCCESS = 'SUCCESS'
        FAILED = 'FAILED'

    report_id : Mapped[uuid.UUID] = mapped_column(primary_key=True, nullable=False, default=uuid.uuid4)
    report_csv : Mapped[str] = mapped_column(nullable=True)
    status : Mapped[PollingStatus] = mapped_column(nullable=False, default=PollingStatus.PENDING)
    created_at : Mapped[str] = mapped_column(nullable=False, server_default=func.now())

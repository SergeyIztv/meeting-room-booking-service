from sqlalchemy import Column, ForeignKey, Integer, Time
from sqlalchemy.orm import relationship
from app.core.database import Base


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    room = relationship("Room", back_populates="slots")
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

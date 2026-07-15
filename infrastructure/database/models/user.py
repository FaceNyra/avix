from sqlalchemy import Column, Integer, String, Enum, ForeignKey, BigInteger, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.enums import Role
from infrastructure.database.base import Base

class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	tg_id = Column(BigInteger, index=True)

	username = Column(String, index=True)
	first_name = Column(String, index=True)
	last_name = Column(String, index=True)

	is_active = Column(Boolean, default=True)
	role = Column(Enum(Role), default=Role.USER)

	created_at = Column(DateTime, default=func.now())
	updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
	
from sqlalchemy.orm import Mapped, mapped_column
from core.models.base import Base
class Link(Base):
    __tablename__ = 'links'
    url: Mapped[str] = mapped_column(unique=True)

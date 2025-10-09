"""SQLAlchemy ORM models mirroring schema.sql."""

from sqlalchemy import String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Station(Base):
    __tablename__ = "stations"
    
    station_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    emergency_buffer: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    connectors: Mapped[list["Connector"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )
    partners: Mapped[list["Partner"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )

class Connector(Base):
    __tablename__ = "connectors"
    
    connector_id: Mapped[str] = mapped_column(String, primary_key=True)
    station_id: Mapped[str] = mapped_column(
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False
    )
    type: Mapped[str] = mapped_column(String, nullable=False)
    kw: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    start_success_rate: Mapped[float] = mapped_column(Float, default=0.9, nullable=False)
    soft_fault_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mttr_h: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trust_badge: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    station: Mapped["Station"] = relationship(back_populates="connectors")

class Session(Base):
    __tablename__ = "sessions"
    
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    connector_id: Mapped[str] = mapped_column(
        ForeignKey("connectors.connector_id"), nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    start_ts: Mapped[str | None] = mapped_column(String, nullable=True)
    stop_ts: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    delivered_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

class Reservation(Base):
    __tablename__ = "reservations"
    
    reservation_id: Mapped[str] = mapped_column(String, primary_key=True)
    station_id: Mapped[str] = mapped_column(
        ForeignKey("stations.station_id"), nullable=False
    )
    connector_id: Mapped[str] = mapped_column(
        ForeignKey("connectors.connector_id"), nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    eta_min: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[str] = mapped_column(String, nullable=False)
    promised_start_min: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)

class Partner(Base):
    __tablename__ = "partners"
    
    partner_id: Mapped[str] = mapped_column(String, primary_key=True)
    station_id: Mapped[str] = mapped_column(
        ForeignKey("stations.station_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    offer: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    station: Mapped["Station"] = relationship(back_populates="partners")

class PointsLedger(Base):
    __tablename__ = "points_ledger"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    ts: Mapped[str] = mapped_column(String, nullable=False)

class Intervention(Base):
    __tablename__ = "interventions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    station_id: Mapped[str | None] = mapped_column(String, nullable=True)
    connector_id: Mapped[str | None] = mapped_column(String, nullable=True)
    promised_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
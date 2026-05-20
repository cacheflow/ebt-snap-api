from sqlalchemy import BigInteger, Float, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    record_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    store_name: Mapped[str | None] = mapped_column(Text)
    store_street_address: Mapped[str | None] = mapped_column(Text)
    additional_address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text, index=True)
    state: Mapped[str | None] = mapped_column(Text, index=True)
    zip_code: Mapped[str | None] = mapped_column(Text, index=True)
    zip4: Mapped[str | None] = mapped_column(Text)
    county: Mapped[str | None] = mapped_column(Text)
    store_type: Mapped[str | None] = mapped_column(Text, index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    incentive_program: Mapped[str | None] = mapped_column(Text)
    grantee_name: Mapped[str | None] = mapped_column(Text)
    object_id: Mapped[int | None] = mapped_column(BigInteger)

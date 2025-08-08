from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import ForeignKey, Table, Column, Integer, DateTime, String
from typing import List, Optional
from datetime import datetime, timezone


# Smart base class that automatically sets a table name that works
# 95% of the time: User -> user, UserEvent -> user_event
class Base(AsyncAttrs, DeclarativeBase):
    table_name: str | None = None

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Convert camel case to snake case. Example: CamelCase -> camel_case"""
        if cls.table_name is not None:
            return cls.table_name

        name = cls.__name__
        return "".join(["_" + i.lower() if i.isupper() else i for i in name]).lstrip("_")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


user_client_association = Table(
    "user_client_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("client_id", Integer, ForeignKey("client.id"), primary_key=True),
)

user_listing_association = Table(
    "user_listing_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("listing_id", Integer, ForeignKey("listing.id"), primary_key=True),
)

client_application_association = Table(
    "client_application_association",
    Base.metadata,
    Column("client_id", Integer, ForeignKey("client.id"), primary_key=True),
    Column("application_id", Integer, ForeignKey("application.id"), primary_key=True),
)

client_context_association = Table(
    "client_context_association",
    Base.metadata,
    Column("client_id", Integer, ForeignKey("client.id"), primary_key=True),
    Column("client_context_id", Integer, ForeignKey("client_context.id"), primary_key=True),
)

listing_context_association = Table(
    "listing_context_association",
    Base.metadata,
    Column("listing_id", Integer, ForeignKey("listing.id"), primary_key=True),
    Column("listing_context_id", Integer, ForeignKey("listing_context.id"), primary_key=True),
)

application_context_association = Table(
    "application_context_association",
    Base.metadata,
    Column("application_id", Integer, ForeignKey("application.id"), primary_key=True),
    Column("application_context_id", Integer, ForeignKey("application_context.id"), primary_key=True),
)

provider_context_association = Table(
    "provider_context_association",
    Base.metadata,
    Column("provider_id", Integer, ForeignKey("provider.id"), primary_key=True),
    Column("provider_context_id", Integer, ForeignKey("provider_context.id"), primary_key=True),
)


class User(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    
    clients: Mapped[List["Client"]] = relationship(secondary=user_client_association, back_populates="users", lazy="select")
    listings: Mapped[List["Listing"]] = relationship(secondary=user_listing_association, back_populates="users", lazy="select")
    user_context: Mapped[Optional["UserContext"]] = relationship(back_populates="user", lazy="select", uselist=False)


class Client(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    users: Mapped[List["User"]] = relationship(secondary=user_client_association, back_populates="clients", lazy="select")
    applications: Mapped[List["Application"]] = relationship(secondary=client_application_association, back_populates="clients", lazy="select")
    client_contexts: Mapped[List["ClientContext"]] = relationship(secondary=client_context_association, back_populates="clients", lazy="select")


class Application(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))
    
    listing: Mapped["Listing"] = relationship(back_populates="applications", lazy="select")
    clients: Mapped[List["Client"]] = relationship(secondary=client_application_association, back_populates="applications", lazy="select")
    application_contexts: Mapped[List["ApplicationContext"]] = relationship(secondary=application_context_association, back_populates="applications", lazy="select")
    document_sections: Mapped[List["DocumentSection"]] = relationship(back_populates="application", lazy="select")


class Listing(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("provider.id"))
    
    provider: Mapped["Provider"] = relationship(back_populates="listings", lazy="select")
    users: Mapped[List["User"]] = relationship(secondary=user_listing_association, back_populates="listings", lazy="select")
    listing_contexts: Mapped[List["ListingContext"]] = relationship(secondary=listing_context_association, back_populates="listings", lazy="select")
    applications: Mapped[List["Application"]] = relationship(back_populates="listing", lazy="select")


class Provider(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    listings: Mapped[List["Listing"]] = relationship(back_populates="provider", lazy="select")
    provider_contexts: Mapped[List["ProviderContext"]] = relationship(secondary=provider_context_association, back_populates="providers", lazy="select")


class UserContext(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    
    user: Mapped["User"] = relationship(back_populates="user_context", lazy="select")


class ClientContext(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    clients: Mapped[List["Client"]] = relationship(secondary=client_context_association, back_populates="client_contexts", lazy="select")


class ListingContext(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    listings: Mapped[List["Listing"]] = relationship(secondary=listing_context_association, back_populates="listing_contexts", lazy="select")


class ApplicationContext(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    applications: Mapped[List["Application"]] = relationship(secondary=application_context_association, back_populates="application_contexts", lazy="select")


class ProviderContext(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    providers: Mapped[List["Provider"]] = relationship(secondary=provider_context_association, back_populates="provider_contexts", lazy="select")


class DocumentSection(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("application.id"))
    
    application: Mapped["Application"] = relationship(back_populates="document_sections", lazy="select")
    document_comments: Mapped[List["DocumentComment"]] = relationship(back_populates="document_section", lazy="select")


class DocumentComment(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    document_section_id: Mapped[int] = mapped_column(ForeignKey("document_section.id"))
    
    document_section: Mapped["DocumentSection"] = relationship(back_populates="document_comments", lazy="select")

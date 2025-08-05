from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import ForeignKey, Table, Column, Integer
from typing import List, Optional


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


# Association tables for many-to-many relationships
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


class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Many-to-many relationships
    clients: Mapped[List["Client"]] = relationship(secondary=user_client_association, back_populates="users", lazy="select")
    listings: Mapped[List["Listing"]] = relationship(secondary=user_listing_association, back_populates="users", lazy="select")
    
    # One-to-one relationship (optional on User side)
    user_context: Mapped["UserContext" | None] = relationship(back_populates="user", lazy="select", uselist=False)


class Client(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Many-to-many relationships
    users: Mapped[List["User"]] = relationship(secondary=user_client_association, back_populates="clients", lazy="select")
    applications: Mapped[List["Application"]] = relationship(secondary=client_application_association, back_populates="clients", lazy="select")
    client_contexts: Mapped[List["ClientContext"]] = relationship(secondary=client_context_association, back_populates="clients", lazy="select")


class Application(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))
    
    # Many-to-one relationship
    listing: Mapped["Listing"] = relationship(back_populates="applications", lazy="select")
    
    # Many-to-many relationships
    clients: Mapped[List["Client"]] = relationship(secondary=client_application_association, back_populates="applications", lazy="select")
    application_contexts: Mapped[List["ApplicationContext"]] = relationship(secondary=application_context_association, back_populates="applications", lazy="select")
    
    # One-to-many relationships
    document_sections: Mapped[List["DocumentSection"]] = relationship(back_populates="application", lazy="select")


class Listing(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("provider.id"))
    
    # Many-to-one relationship
    provider: Mapped["Provider"] = relationship(back_populates="listings", lazy="select")
    
    # Many-to-many relationships
    users: Mapped[List["User"]] = relationship(secondary=user_listing_association, back_populates="listings", lazy="select")
    listing_contexts: Mapped[List["ListingContext"]] = relationship(secondary=listing_context_association, back_populates="listings", lazy="select")
    
    # One-to-many relationships
    applications: Mapped[List["Application"]] = relationship(back_populates="listing", lazy="select")


class Provider(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # One-to-many relationships
    listings: Mapped[List["Listing"]] = relationship(back_populates="provider", lazy="select")
    provider_contexts: Mapped[List["ProviderContext"]] = relationship(secondary=provider_context_association, back_populates="providers", lazy="select")


class UserContext(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    
    # Many-to-one relationship
    user: Mapped["User"] = relationship(back_populates="user_context", lazy="select")


class ClientContext(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Many-to-many relationships
    clients: Mapped[List["Client"]] = relationship(secondary=client_context_association, back_populates="client_contexts", lazy="select")


class ListingContext(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Many-to-many relationships
    listings: Mapped[List["Listing"]] = relationship(secondary=listing_context_association, back_populates="listing_contexts", lazy="select")


class ApplicationContext(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Many-to-many relationships
    applications: Mapped[List["Application"]] = relationship(secondary=application_context_association, back_populates="application_contexts", lazy="select")


class ProviderContext(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Many-to-many relationships
    providers: Mapped[List["Provider"]] = relationship(secondary=provider_context_association, back_populates="provider_contexts", lazy="select")


class DocumentSection(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("application.id"))
    
    # Many-to-one relationship
    application: Mapped["Application"] = relationship(back_populates="document_sections", lazy="select")
    
    # One-to-many relationships
    document_comments: Mapped[List["DocumentComment"]] = relationship(back_populates="document_section", lazy="select")


class DocumentComment(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    document_section_id: Mapped[int] = mapped_column(ForeignKey("document_section.id"))
    
    # Many-to-one relationship
    document_section: Mapped["DocumentSection"] = relationship(back_populates="document_comments", lazy="select")





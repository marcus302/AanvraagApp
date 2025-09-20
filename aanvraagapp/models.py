from datetime import datetime, timezone, date
from typing import List, Optional, Literal
from aanvraagapp.types import TargetAudience, FinancialInstrument

from sqlalchemy import Column, ForeignKey, Integer, String, Table, types, CheckConstraint, Boolean, Date
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from enum import Enum
from numpy.typing import NDArray
import numpy as np

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
        return "".join(["_" + i.lower() if i.isupper() else i for i in name]).lstrip(
            "_"
        )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        types.DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        types.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


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


listing_target_audience_label_association = Table(
    "listing_target_audience_label_association",
    Base.metadata,
    Column("listing_id", Integer, ForeignKey("listing.id"), primary_key=True),
    Column("target_audience_label_id", Integer, ForeignKey("target_audience_label.id"), primary_key=True),
)

# client_document_association = Table(
#     "client_document_association",
#     Base.metadata,
#     Column("client_id", Integer, ForeignKey("client.id"), primary_key=True),
#     Column(
#         "client_document_id", Integer, ForeignKey("client_document.id"), primary_key=True
#     ),
# )

# listing_document_association = Table(
#     "listing_document_association",
#     Base.metadata,
#     Column("listing_id", Integer, ForeignKey("listing.id"), primary_key=True),
#     Column(
#         "listing_document_id",
#         Integer,
#         ForeignKey("listing_document.id"),
#         primary_key=True,
#     ),
# )

# application_document_association = Table(
#     "application_document_association",
#     Base.metadata,
#     Column("application_id", Integer, ForeignKey("application.id"), primary_key=True),
#     Column(
#         "application_document_id",
#         Integer,
#         ForeignKey("application_document.id"),
#         primary_key=True,
#     ),
# )

# provider_document_association = Table(
#     "provider_document_association",
#     Base.metadata,
#     Column("provider_id", Integer, ForeignKey("provider.id"), primary_key=True),
#     Column(
#         "provider_document_id",
#         Integer,
#         ForeignKey("provider_document.id"),
#         primary_key=True,
#     ),
# )


class User(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    clients: Mapped[List["Client"]] = relationship(
        secondary=user_client_association, back_populates="users", lazy="select"
    )
    listings: Mapped[List["Listing"]] = relationship(
        secondary=user_listing_association, back_populates="users", lazy="select"
    )
    user_document: Mapped[Optional["UserDocument"]] = relationship(
        back_populates="user", lazy="select", uselist=False
    )


class Client(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    website: Mapped[str] = mapped_column(String, nullable=False)

    business_identity: Mapped[TargetAudience | None] = mapped_column(String, nullable=True)
    audience_desc: Mapped[str | None] = mapped_column(String, nullable=True)

    users: Mapped[List["User"]] = relationship(
        secondary=user_client_association, back_populates="clients", lazy="select"
    )
    applications: Mapped[List["Application"]] = relationship(
        secondary=client_application_association,
        back_populates="clients",
        lazy="select",
    )
    websites: Mapped[List["Webpage"]] = relationship(
        "Webpage",
        primaryjoin="and_(Client.id==foreign(Webpage.owner_id), Webpage.owner_type=='client')",
        back_populates="client",
        cascade="all, delete-orphan",
        overlaps="listing,websites",
    )
    # client_documents: Mapped[List["ClientDocument"]] = relationship(
    #     secondary=client_document_association, back_populates="clients", lazy="select"
    # )


class Application(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))

    listing: Mapped["Listing"] = relationship(
        back_populates="applications", lazy="select"
    )
    clients: Mapped[List["Client"]] = relationship(
        secondary=client_application_association,
        back_populates="applications",
        lazy="select",
    )
    # application_documents: Mapped[List["ApplicationDocument"]] = relationship(
    #     secondary=application_document_association,
    #     back_populates="applications",
    #     lazy="select",
    # )
    document_sections: Mapped[List["DocumentSection"]] = relationship(
        back_populates="application", lazy="select"
    )


class Listing(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("provider.id"))

    website: Mapped[str] = mapped_column(String, nullable=False)

    is_open: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    opens_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    closes_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_checked: Mapped[date | None] = mapped_column(Date, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    financial_instrument: Mapped[FinancialInstrument | None] = mapped_column(String, nullable=True)
    target_audience_desc: Mapped[str | None] = mapped_column(String, nullable=True)

    provider: Mapped["Provider"] = relationship(
        back_populates="listings", lazy="select"
    )
    users: Mapped[List["User"]] = relationship(
        secondary=user_listing_association, back_populates="listings", lazy="select"
    )
    websites: Mapped[list["Webpage"]] = relationship(
        "Webpage",
        primaryjoin="and_(Listing.id==foreign(Webpage.owner_id), Webpage.owner_type=='listing')",
        back_populates="listing",
        cascade="all, delete-orphan",
        overlaps="client,websites",
    )
    applications: Mapped[List["Application"]] = relationship(
        back_populates="listing", lazy="select"
    )
    target_audience_labels: Mapped[List["TargetAudienceLabel"]] = relationship(
        secondary=listing_target_audience_label_association,
        back_populates="listings",
        lazy="select",
    )


class TargetAudienceLabel(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    listings: Mapped[List["Listing"]] = relationship(
        secondary=listing_target_audience_label_association,
        back_populates="target_audience_labels",
        lazy="select",
    )


class Provider(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str] = mapped_column(String, nullable=False)

    listings: Mapped[List["Listing"]] = relationship(
        back_populates="provider", lazy="select"
    )
    # provider_documents: Mapped[List["ProviderDocument"]] = relationship(
    #     secondary=provider_document_association,
    #     back_populates="providers",
    #     lazy="select",
    # )


class UserDocument(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    # This will contain the user's own preferences.
    content: Mapped[str] = mapped_column(String, nullable=True)
    user: Mapped["User"] = relationship(back_populates="user_document", lazy="select")


class WebpageOwnerType(str, Enum):
    LISTING = "listing"
    CLIENT = "client"


class Webpage(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)

    owner_type: Mapped[WebpageOwnerType] = mapped_column(String, nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)

    url: Mapped[str] = mapped_column(String, nullable=False)
    original_content: Mapped[str] = mapped_column(String, nullable=True)
    filtered_content: Mapped[str] = mapped_column(String, nullable=True)
    markdown_content: Mapped[str] = mapped_column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("owner_type IN ('client', 'listing')", name='webpage_valid_owner_type'),
    )

    listing: Mapped[Listing] = relationship(
        primaryjoin="and_(foreign(Webpage.owner_id)==Listing.id, Webpage.owner_type=='listing')",
        back_populates="websites",
        overlaps="client,websites",
    )
    
    client: Mapped[Client] = relationship(
        primaryjoin="and_(foreign(Webpage.owner_id)==Client.id, Webpage.owner_type=='client')",
        back_populates="websites",
        overlaps="listing,websites",
    )

    chunks = relationship(
        "Chunk",
        primaryjoin="and_(foreign(Webpage.id)==Chunk.owner_id, Chunk.owner_type=='webpage')",
        back_populates="webpage",
    )


class ChunkOwnerType(str, Enum):
    WEBPAGE = "webpage"


class Chunk(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)

    owner_type: Mapped[ChunkOwnerType] = mapped_column(String, nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)

    content: Mapped[str] = mapped_column(String, nullable=False)
    emb: Mapped[NDArray[np.float32]] = mapped_column(Vector(768))

    __table_args__ = (
        CheckConstraint("owner_type IN ('webpage')", name='chunk_valid_owner_type'),
    )

    webpage: Mapped[Webpage] = relationship(
        primaryjoin="and_(Chunk.owner_id==foreign(Webpage.id), Chunk.owner_type=='webpage')",
        back_populates="chunks"
    )



# class ClientDocument(TimestampMixin, Base):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     doc_type: Mapped[DocumentType] = mapped_column(String, nullable=False)
#     uri: Mapped[str] = mapped_column(String, nullable=False)
#     clients: Mapped[List["Client"]] = relationship(
#         secondary=client_document_association,
#         back_populates="client_documents",
#         lazy="select",
#     )
#     chunks: Mapped[List["ClientDocumentChunk"]] = relationship(
#         back_populates="document", lazy="select"
#     )


# class ClientDocumentChunk(Base):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     document_id: Mapped[int] = mapped_column(ForeignKey("client_document.id"))
#     content: Mapped[str] = mapped_column(String, nullable=False)
#     emb: Mapped[NDArray[np.float32]] = mapped_column(Vector(3072))
#     document: Mapped["ClientDocument"] = relationship(
#         back_populates="chunks", lazy="select"
#     )


# class ListingDocument(TimestampMixin, Base):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     doc_type: Mapped[DocumentType] = mapped_column(String, nullable=False)
#     uri: Mapped[str] = mapped_column(String, nullable=False)
#     listings: Mapped[List["Listing"]] = relationship(
#         secondary=listing_document_association,
#         back_populates="listing_documents",
#         lazy="select",
#     )
#     chunks: Mapped[List["ListingDocumentChunk"]] = relationship(
#         back_populates="document", lazy="select"
#     )


# class ListingDocumentChunk(Base):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     document_id: Mapped[int] = mapped_column(ForeignKey("listing_document.id"))
#     content: Mapped[str] = mapped_column(String, nullable=False)
#     emb: Mapped[NDArray[np.float32]] = mapped_column(Vector(3072))
#     document: Mapped["ListingDocument"] = relationship(
#         back_populates="chunks", lazy="select"
#     )


# class ApplicationDocument(TimestampMixin, Base):
#     id: Mapped[int] = mapped_column(primary_key=True)

#     applications: Mapped[List["Application"]] = relationship(
#         secondary=application_document_association,
#         back_populates="application_documents",
#         lazy="select",
#     )


# class ProviderDocument(TimestampMixin, Base):
#     id: Mapped[int] = mapped_column(primary_key=True)

#     providers: Mapped[List["Provider"]] = relationship(
#         secondary=provider_document_association,
#         back_populates="provider_documents",
#         lazy="select",
#     )


class DocumentSection(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("application.id"))

    application: Mapped["Application"] = relationship(
        back_populates="document_sections", lazy="select"
    )
    document_comments: Mapped[List["DocumentComment"]] = relationship(
        back_populates="document_section", lazy="select"
    )


class DocumentComment(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    document_section_id: Mapped[int] = mapped_column(ForeignKey("document_section.id"))

    document_section: Mapped["DocumentSection"] = relationship(
        back_populates="document_comments", lazy="select"
    )

# models.py
import uuid
from datetime import datetime, date
from sqlalchemy import (
    String, Date, Text, JSON, TIMESTAMP, ForeignKey, Integer, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database.connection import Base
from pgvector.sqlalchemy import Vector


EMBED_DIM = 768

class SermonFile(Base):
    __tablename__ = "sermon_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(String, nullable=False)  # 'audio' | 'text'
    original_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    preacher: Mapped[str | None] = mapped_column(String, nullable=True)
    occasion: Mapped[str | None] = mapped_column(String, nullable=True)
    sermon_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bible_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[dict | list | None] = mapped_column(JSON, default=list)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    chunks: Mapped[list["SermonChunk"]] = relationship(
        "SermonChunk", back_populates="file", cascade="all, delete-orphan"
    )


class SermonChunk(Base):
    __tablename__ = "sermon_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sermon_files.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str | None] = mapped_column(String, nullable=True)  # 'introduction' | 'scripture_reading' | 'body'
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # vektor mező
    embedding = mapped_column(Vector(EMBED_DIM), nullable=False)

    file: Mapped[SermonFile] = relationship("SermonFile", back_populates="chunks")


# --- Indexek ---
# IVFFlat cosine index a vektorra (lists paraméterrel)
Index(
    "idx_chunks_embedding_ivf",
    SermonChunk.embedding,
    postgresql_using="ivfflat",
    postgresql_with={"lists": 100},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
Index("idx_files_date", SermonFile.sermon_date)
-- pgvector bővítmény
CREATE EXTENSION IF NOT EXISTS vector;

-- Forrás fájl / rekord szintű meta
CREATE TABLE IF NOT EXISTS sermon_files (
  id               UUID PRIMARY KEY,
  source_type      TEXT NOT NULL,              -- 'audio' | 'text'
  original_filename TEXT,
  preacher         TEXT,
  occasion         TEXT,                       -- pl. "Vasárnapi istentisztelet"
  sermon_date      DATE,
  bible_ref        TEXT,
  tags             JSONB DEFAULT '[]'::jsonb,  -- pl. 20 címke
  raw_text         TEXT,                       -- ha megőrzöd
  corrected_text   TEXT NOT NULL,              -- EBBŐL készül az embedding
  created_at       TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Chunkok a kereséshez (időbélyeg nélkül)
CREATE TABLE IF NOT EXISTS sermon_chunks (
  id           UUID PRIMARY KEY,
  file_id      UUID NOT NULL REFERENCES sermon_files(id) ON DELETE CASCADE,
  chunk_index  INTEGER NOT NULL,               -- 0..N
  char_start   INTEGER NOT NULL,               -- részlet kezdete (karakter index)
  char_end     INTEGER NOT NULL,               -- részlet vége (karakter index)
  section      TEXT,                           -- opcionális: 'introduction'|'scripture_reading'|'body'
  text         TEXT NOT NULL,                  -- a chunk szöveg
  embedding    VECTOR(768) NOT NULL            -- dimenziót igazítsd a modelledhez
);

-- Vektor index (IVFFlat, cosine)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivf
  ON sermon_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Gyakori lekérdezésekhez
CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON sermon_chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_files_date ON sermon_files(sermon_date);
CREATE INDEX IF NOT EXISTS idx_files_tags ON sermon_files USING GIN (tags);
-- Create the documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    resume TEXT,
    jd TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP DEFAULT NULL
);

-- Add descriptions to the columns
COMMENT ON COLUMN documents.id IS 'Unique identifier for each document collection';
COMMENT ON COLUMN documents.name IS 'Name of the collection of documents (must be unique)';
COMMENT ON COLUMN documents.resume IS 'Resume storage (average 8192 characters)';
COMMENT ON COLUMN documents.jd IS 'The job description accompanying the resume (average 8192 characters)';
COMMENT ON COLUMN documents.summary IS 'A summary for this collection of documents';
COMMENT ON COLUMN documents.created_at IS 'Timestamp when record was created';
COMMENT ON COLUMN documents.updated_at IS 'Timestamp when record was last updated';
COMMENT ON COLUMN documents.deleted_at IS 'Timestamp when record was soft-deleted (NULL if active)';

-- Create index on name for faster lookups and uniqueness
CREATE INDEX IF NOT EXISTS idx_documents_name ON documents(name);

-- Create partial index for active (non-deleted) documents
CREATE INDEX IF NOT EXISTS idx_documents_active ON documents(deleted_at) WHERE deleted_at IS NULL;

-- Create trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

# aliciadata-chat-admin
A private and locally installed admin interface for the aliciadata-chat public-facing app.

## Prerequisites

- PostgreSQL 17 installed and running locally
- Python 3.10+ installed
- uv package manager installed

### Installing uv

If you don't have `uv` installed, you can install it via pip:

```bash
pip install uv
```

Or follow the official installation guide at https://docs.astral.sh/uv/

## Project Setup

### 1. Database Setup

First, create the PostgreSQL database and run the migration:

```bash
# Create database
createdb aliciadata_chat

# Run migration
psql -d aliciadata_chat -f migrations/001_create_documents_table.sql
```

### 2. Environment Configuration

Copy the environment template and configure your database credentials:

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your PostgreSQL credentials
# Use your preferred editor (nano, vim, code, etc.)
nano .env
```

Update the `.env` file with your actual PostgreSQL credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aliciadata_chat
DB_USER=your_username
DB_PASSWORD=your_password
```

### 3. Install Dependencies with uv

Initialize the project and install all dependencies:

```bash
# Sync dependencies from pyproject.toml
uv sync
```

This will:
- Create a virtual environment in `.venv/`
- Install all project dependencies (gradio, psycopg2-binary, python-dotenv)
- Install development dependencies (black, pytest)

### 4. Run the Application

Start the Gradio application:

```bash
# Run the application
uv run python src/app.py
```

The application will open automatically in your browser at `http://localhost:7860`

## Usage

### Creating a New Document

1. Fill in the Name field (required, must be unique)
2. Paste job description in "Job Description" field
3. Paste resume in "Resume" field
4. Optionally add a summary
5. Click "Submit or Update"

### Searching Documents

1. Type in the "Search by Name" field
2. Table updates automatically (case-insensitive partial match)
3. Click "Clear Search" to show all documents

### Editing a Document

1. Click on any row in the table to select it
2. Full document data loads into form fields
3. Modify any fields (Name must remain unique)
4. Click "Submit or Update" to save changes

### Deleting a Document

1. Click on a row in the table to select it
2. "Delete" button becomes enabled
3. Click "Delete" to soft-delete the document
4. Document is hidden from view but remains in database

### Clearing the Form

Click "Clear Form" to reset all fields without saving

## Key Features

- **Unique Names**: Document names must be unique (enforced by database)
- **Soft Delete**: Deleted documents are hidden but not permanently removed
- **Search**: Filter documents by name (case-insensitive)
- **Large Text Support**: Resume and JD fields support ~8KB of text
- **Auto-timestamps**: Created and updated timestamps are automatic
- **Table Preview**: Resume/JD show first 100 characters in table

## Development

### Format Code with Black

```bash
uv run black src/
```

### Check Formatting

```bash
uv run black --check src/
```

### Run Tests

```bash
uv run pytest
```

### Adding New Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

## Database Management

### View Soft-Deleted Documents

```sql
SELECT id, name, deleted_at
FROM documents
WHERE deleted_at IS NOT NULL
ORDER BY deleted_at DESC;
```

### Restore a Soft-Deleted Document

```sql
UPDATE documents
SET deleted_at = NULL
WHERE id = <document_id>;
```

### Permanently Delete (Hard Delete)

```sql
DELETE FROM documents WHERE id = <document_id>;
```

### Purge All Soft-Deleted Documents

```sql
DELETE FROM documents WHERE deleted_at IS NOT NULL;
```

## Troubleshooting

### Connection Errors

- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `.env` file
- Ensure database exists: `psql -l | grep aliciadata_chat`

### Permission Errors

- Ensure database user has CREATE/INSERT/UPDATE/DELETE privileges
- Grant permissions: `GRANT ALL PRIVILEGES ON DATABASE aliciadata_chat TO your_username;`

### Duplicate Name Error

- Document names must be unique
- Check existing names: `SELECT name FROM documents WHERE deleted_at IS NULL;`
- Use search to find existing document
- Choose a different name or update the existing document

### Port Conflicts

- Gradio default port 7860 can be changed in `src/app.py`
- Modify: `demo.launch(server_port=YOUR_PORT)`

### Large Text Issues

- PostgreSQL TEXT type supports up to ~1GB
- 8KB average is well within limits
- If UI feels slow, check system resources

### uv Issues

- If `uv sync` fails, try removing `.venv/` and running again
- Ensure you're using Python 3.10 or higher: `python --version`
- Check uv version: `uv --version`
- Update uv: `pip install --upgrade uv`

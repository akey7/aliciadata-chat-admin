"""Database module for documents CRUD operations."""

import os
from typing import List, Optional, Tuple

import psycopg2
import psycopg2.errors
import psycopg2.extensions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_connection() -> psycopg2.extensions.connection:
    """
    Establish database connection using environment variables.

    Returns:
        psycopg2 connection object

    Raises:
        psycopg2.Error: If connection fails
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "aliciadata_chat"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        return conn
    except psycopg2.Error as e:
        error_msg = f"Failed to connect to database: {str(e)}"
        print(error_msg)
        raise


def initialize_database() -> bool:
    """
    Run migration and verify database is ready.

    Returns:
        True if database is initialized successfully, False otherwise
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Check if documents table exists
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'documents'
                )
                """
            )
            exists = cur.fetchone()[0]
            conn.close()
            return exists
    except psycopg2.Error as e:
        error_msg = f"Database initialization check failed: {str(e)}"
        print(error_msg)
        return False


def get_all_documents(search_name: str = "") -> List[Tuple]:
    """
    Retrieve all active (non-deleted) documents.

    If search_name provided, filter by name (case-insensitive ILIKE).
    Order by updated_at DESC.

    Args:
        search_name: Optional search term to filter by name

    Returns:
        List of tuples: (id, name, resume, jd, summary, created_at, updated_at)

    Raises:
        psycopg2.Error: If database operation fails
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            if search_name:
                cur.execute(
                    """
                    SELECT id, name, resume, jd, summary, created_at, updated_at
                    FROM documents
                    WHERE deleted_at IS NULL AND name ILIKE %s
                    ORDER BY updated_at DESC
                    """,
                    (f"%{search_name}%",),
                )
            else:
                cur.execute(
                    """
                    SELECT id, name, resume, jd, summary, created_at, updated_at
                    FROM documents
                    WHERE deleted_at IS NULL
                    ORDER BY updated_at DESC
                    """
                )
            results = cur.fetchall()
            return results
    except psycopg2.Error as e:
        error_msg = f"Database error while fetching documents: {str(e)}"
        print(error_msg)
        raise
    finally:
        if conn:
            conn.close()


def get_document_by_id(doc_id: int) -> Optional[Tuple]:
    """
    Retrieve a single active document by ID.

    Args:
        doc_id: The ID of the document to retrieve

    Returns:
        Tuple: (id, name, resume, jd, summary, created_at, updated_at) or None if not found

    Raises:
        psycopg2.Error: If database operation fails
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, resume, jd, summary, created_at, updated_at
                FROM documents
                WHERE id = %s AND deleted_at IS NULL
                """,
                (doc_id,),
            )
            result = cur.fetchone()
            return result
    except psycopg2.Error as e:
        error_msg = f"Database error while fetching document {doc_id}: {str(e)}"
        print(error_msg)
        raise
    finally:
        if conn:
            conn.close()


def create_document(
    name: str, resume: str, jd: str, summary: str
) -> Tuple[bool, str, Optional[int]]:
    """
    Insert new document and return (success, message, id).

    Handle UNIQUE constraint violation on name.

    Args:
        name: Unique name for the document collection
        resume: Resume text content
        jd: Job description text content
        summary: Summary text

    Returns:
        Tuple of (success: bool, message: str, doc_id: Optional[int])
        - (True, "Success message", doc_id) on success
        - (False, "Error message", None) on failure

    Raises:
        ValueError: If name is empty
    """
    # Validate name
    if not name or not name.strip():
        return False, "Name is required", None

    name = name.strip()
    resume = resume.strip() if resume else ""
    jd = jd.strip() if jd else ""
    summary = summary.strip() if summary else ""

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (name, resume, jd, summary)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (name, resume, jd, summary),
            )
            doc_id = cur.fetchone()[0]
            conn.commit()
            return True, f"Document '{name}' created successfully", doc_id

    except psycopg2.errors.UniqueViolation:
        if conn:
            conn.rollback()
        return False, f"Name '{name}' already exists", None

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        error_msg = f"Database error: {str(e)}"
        print(error_msg)
        return False, error_msg, None

    finally:
        if conn:
            conn.close()


def update_document(
    doc_id: int, name: str, resume: str, jd: str, summary: str
) -> Tuple[bool, str]:
    """
    Update existing active document.

    Handle UNIQUE constraint violation if name conflicts with another document.

    Args:
        doc_id: ID of the document to update
        name: Unique name for the document collection
        resume: Resume text content
        jd: Job description text content
        summary: Summary text

    Returns:
        Tuple of (success: bool, message: str)
        - (True, "Success message") on success
        - (False, "Error message") on failure

    Raises:
        ValueError: If name is empty or doc_id is invalid
    """
    # Validate inputs
    if not name or not name.strip():
        return False, "Name is required"

    if doc_id is None or doc_id <= 0:
        return False, "Invalid document ID"

    name = name.strip()
    resume = resume.strip() if resume else ""
    jd = jd.strip() if jd else ""
    summary = summary.strip() if summary else ""

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET name = %s, resume = %s, jd = %s, summary = %s
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id
                """,
                (name, resume, jd, summary, doc_id),
            )
            result = cur.fetchone()
            conn.commit()

            if result:
                return True, f"Document '{name}' updated successfully"
            else:
                return False, "Document not found or already deleted"

    except psycopg2.errors.UniqueViolation:
        if conn:
            conn.rollback()
        return False, f"Name '{name}' already exists"

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        error_msg = f"Database error: {str(e)}"
        print(error_msg)
        return False, error_msg

    finally:
        if conn:
            conn.close()


def soft_delete_document(doc_id: int) -> Tuple[bool, str]:
    """
    Soft delete document by setting deleted_at to CURRENT_TIMESTAMP.

    Only affects active documents (deleted_at IS NULL).

    Args:
        doc_id: The ID of the document to soft delete

    Returns:
        Tuple of (success: bool, message: str)
        - (True, "Document deleted successfully") on success
        - (False, "Error message") on failure

    Raises:
        ValueError: If doc_id is invalid or negative
    """
    if doc_id is None or doc_id <= 0:
        return False, "Invalid document ID"

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id
                """,
                (doc_id,),
            )
            result = cur.fetchone()
            conn.commit()

            if result:
                return True, f"Document {doc_id} deleted successfully"
            else:
                return False, "Document not found or already deleted"

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        error_msg = f"Database error: {str(e)}"
        print(error_msg)
        return False, error_msg

    finally:
        if conn:
            conn.close()


def check_name_exists(name: str, exclude_id: Optional[int] = None) -> bool:
    """
    Check if name exists in active documents.

    If exclude_id provided, ignore that document (for updates).

    Args:
        name: The name to check
        exclude_id: Optional document ID to exclude from the check

    Returns:
        True if name exists, False otherwise
    """
    if not name or not name.strip():
        return False

    name = name.strip()
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            if exclude_id:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM documents
                        WHERE name = %s AND deleted_at IS NULL AND id != %s
                    )
                    """,
                    (name, exclude_id),
                )
            else:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM documents
                        WHERE name = %s AND deleted_at IS NULL
                    )
                    """,
                    (name,),
                )
            exists = cur.fetchone()[0]
            return exists

    except psycopg2.Error as e:
        error_msg = f"Database error while checking name: {str(e)}"
        print(error_msg)
        return False

    finally:
        if conn:
            conn.close()

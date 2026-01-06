"""Tests for database module."""

import os
from unittest.mock import MagicMock, patch

import pytest
import psycopg2.errors

from src.db import (
    check_name_exists,
    create_document,
    get_all_documents,
    get_document_by_id,
    soft_delete_document,
    update_document,
)


class TestCreateDocument:
    """Tests for create_document function."""

    @patch("src.db.get_connection")
    def test_create_document_success(self, mock_get_connection):
        """Test successful document creation."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        # Execute
        success, message, doc_id = create_document(
            "Test Doc", "Resume text", "JD text", "Summary"
        )

        # Assert
        assert success is True
        assert "created successfully" in message
        assert doc_id == 1
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch("src.db.get_connection")
    def test_create_document_empty_name(self, mock_get_connection):
        """Test creating document with empty name fails."""
        success, message, doc_id = create_document("", "Resume", "JD", "Summary")

        assert success is False
        assert "Name is required" in message
        assert doc_id is None

    @patch("src.db.get_connection")
    def test_create_document_duplicate_name(self, mock_get_connection):
        """Test creating document with duplicate name fails."""
        # Setup mock to raise UniqueViolation
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        # Execute
        success, message, doc_id = create_document(
            "Duplicate", "Resume", "JD", "Summary"
        )

        # Assert
        assert success is False
        assert "already exists" in message
        assert doc_id is None
        mock_conn.rollback.assert_called_once()

    @patch("src.db.get_connection")
    def test_create_document_strips_whitespace(self, mock_get_connection):
        """Test that whitespace is stripped from fields."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        create_document("  Test  ", "  Resume  ", "  JD  ", "  Summary  ")

        # Check that execute was called with stripped values
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == ("Test", "Resume", "JD", "Summary")


class TestUpdateDocument:
    """Tests for update_document function."""

    @patch("src.db.get_connection")
    def test_update_document_success(self, mock_get_connection):
        """Test successful document update."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        success, message = update_document(
            1, "Updated Name", "New Resume", "New JD", "New Summary"
        )

        assert success is True
        assert "updated successfully" in message
        mock_conn.commit.assert_called_once()

    @patch("src.db.get_connection")
    def test_update_document_empty_name(self, mock_get_connection):
        """Test updating with empty name fails."""
        success, message = update_document(1, "", "Resume", "JD", "Summary")

        assert success is False
        assert "Name is required" in message

    @patch("src.db.get_connection")
    def test_update_document_invalid_id(self, mock_get_connection):
        """Test updating with invalid ID fails."""
        success, message = update_document(0, "Name", "Resume", "JD", "Summary")

        assert success is False
        assert "Invalid document ID" in message

    @patch("src.db.get_connection")
    def test_update_document_not_found(self, mock_get_connection):
        """Test updating non-existent document."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        success, message = update_document(999, "Name", "Resume", "JD", "Summary")

        assert success is False
        assert "not found" in message.lower()

    @patch("src.db.get_connection")
    def test_update_document_duplicate_name(self, mock_get_connection):
        """Test updating to duplicate name fails."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        success, message = update_document(1, "Existing", "Resume", "JD", "Summary")

        assert success is False
        assert "already exists" in message
        mock_conn.rollback.assert_called_once()


class TestSoftDeleteDocument:
    """Tests for soft_delete_document function."""

    @patch("src.db.get_connection")
    def test_soft_delete_success(self, mock_get_connection):
        """Test successful soft delete."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        success, message = soft_delete_document(1)

        assert success is True
        assert "deleted successfully" in message
        mock_conn.commit.assert_called_once()

    @patch("src.db.get_connection")
    def test_soft_delete_invalid_id(self, mock_get_connection):
        """Test soft delete with invalid ID."""
        success, message = soft_delete_document(0)

        assert success is False
        assert "Invalid document ID" in message

    @patch("src.db.get_connection")
    def test_soft_delete_not_found(self, mock_get_connection):
        """Test soft delete on non-existent document."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        success, message = soft_delete_document(999)

        assert success is False
        assert "not found" in message.lower()


class TestGetAllDocuments:
    """Tests for get_all_documents function."""

    @patch("src.db.get_connection")
    def test_get_all_documents_no_search(self, mock_get_connection):
        """Test getting all documents without search."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "Doc1", "Resume1", "JD1", "Summary1", None, None),
            (2, "Doc2", "Resume2", "JD2", "Summary2", None, None),
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        results = get_all_documents()

        assert len(results) == 2
        assert results[0][1] == "Doc1"
        assert results[1][1] == "Doc2"

    @patch("src.db.get_connection")
    def test_get_all_documents_with_search(self, mock_get_connection):
        """Test getting documents with search filter."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "Test Doc", "Resume", "JD", "Summary", None, None)
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        results = get_all_documents("Test")

        assert len(results) == 1
        # Verify ILIKE pattern was used
        call_args = mock_cursor.execute.call_args[0]
        assert "%Test%" in call_args[1]


class TestGetDocumentById:
    """Tests for get_document_by_id function."""

    @patch("src.db.get_connection")
    def test_get_document_by_id_found(self, mock_get_connection):
        """Test getting document by ID when it exists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            1,
            "Test",
            "Resume",
            "JD",
            "Summary",
            None,
            None,
        )
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        result = get_document_by_id(1)

        assert result is not None
        assert result[1] == "Test"

    @patch("src.db.get_connection")
    def test_get_document_by_id_not_found(self, mock_get_connection):
        """Test getting document by ID when it doesn't exist."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        result = get_document_by_id(999)

        assert result is None


class TestCheckNameExists:
    """Tests for check_name_exists function."""

    @patch("src.db.get_connection")
    def test_check_name_exists_true(self, mock_get_connection):
        """Test checking name that exists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (True,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        exists = check_name_exists("Existing Name")

        assert exists is True

    @patch("src.db.get_connection")
    def test_check_name_exists_false(self, mock_get_connection):
        """Test checking name that doesn't exist."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (False,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        exists = check_name_exists("New Name")

        assert exists is False

    @patch("src.db.get_connection")
    def test_check_name_exists_with_exclude_id(self, mock_get_connection):
        """Test checking name with excluded ID."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (False,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        exists = check_name_exists("Name", exclude_id=1)

        assert exists is False
        # Verify exclude_id was used in query
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == ("Name", 1)

    @patch("src.db.get_connection")
    def test_check_name_exists_empty_name(self, mock_get_connection):
        """Test checking empty name returns False."""
        exists = check_name_exists("")

        assert exists is False

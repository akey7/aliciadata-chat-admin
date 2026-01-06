"""Gradio CRUD application for documents management."""

from typing import Any, List, Optional, Tuple

import gradio as gr

from src.db import (
    create_document,
    get_all_documents,
    get_document_by_id,
    initialize_database,
    soft_delete_document,
    update_document,
)


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to max_length characters, add ellipsis if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if text is None:
        return ""
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def prepare_table_data(documents: List[Tuple]) -> List[List[Any]]:
    """
    Convert database results to display format.

    Args:
        documents: List of document tuples from database

    Returns:
        List of lists formatted for dataframe display
        Format: (id, name, resume_preview, jd_preview, summary, updated_at)
    """
    return [
        [
            doc[0],  # id
            doc[1],  # name
            truncate_text(doc[2], 100),  # resume preview
            truncate_text(doc[3], 100),  # jd preview
            doc[4] or "",  # summary
            doc[6].strftime("%Y-%m-%d %H:%M") if doc[6] else "",  # updated_at
        ]
        for doc in documents
    ]


def load_documents(search_term: str = "") -> List[List[Any]]:
    """
    Load and format documents for display.

    Args:
        search_term: Optional search filter

    Returns:
        Formatted document data for dataframe
    """
    try:
        documents = get_all_documents(search_term)
        return prepare_table_data(documents)
    except Exception as e:
        print(f"Error loading documents: {e}")
        return []


def on_search(search_term: str) -> gr.Dataframe:
    """
    Filter documents by name (case-insensitive).

    Args:
        search_term: Search term to filter by

    Returns:
        Updated dataframe with filtered results
    """
    data = load_documents(search_term)
    return gr.Dataframe(value=data)


def on_clear_search() -> Tuple[str, gr.Dataframe]:
    """
    Reset search and show all active documents.

    Returns:
        Tuple of (empty search string, updated dataframe)
    """
    data = load_documents("")
    return "", gr.Dataframe(value=data)


def is_form_empty(jd: str, resume: str, summary: str, name: str) -> bool:
    """
    Check if all form fields are empty.

    Args:
        jd: Job description text
        resume: Resume text
        summary: Summary text
        name: Name text

    Returns:
        True if all fields are empty, False otherwise
    """
    return not any([jd.strip(), resume.strip(), summary.strip(), name.strip()])


def on_row_select(
    evt: gr.SelectData, dataframe_data: Any
) -> Tuple[str, str, str, str, int, str, gr.Button, gr.Button]:
    """
    Populate form fields when a row is clicked.

    Args:
        evt: SelectData event containing row index
        dataframe_data: Current dataframe data (pandas DataFrame or list)

    Returns:
        Tuple of (jd, resume, summary, name, selected_id, original_name, delete_button, clear_form_button)
    """
    # Handle pandas DataFrame
    import pandas as pd
    if isinstance(dataframe_data, pd.DataFrame):
        if dataframe_data.empty or evt.index[0] >= len(dataframe_data):
            return "", "", "", "", None, None, gr.Button(interactive=False), gr.Button(interactive=False)
        row = dataframe_data.iloc[evt.index[0]]
        doc_id = int(row.iloc[0])
    else:
        # Handle list
        if not dataframe_data or evt.index[0] >= len(dataframe_data):
            return "", "", "", "", None, None, gr.Button(interactive=False), gr.Button(interactive=False)
        row = dataframe_data[evt.index[0]]
        doc_id = row[0]

    # Fetch FULL document data from database (not truncated preview)
    try:
        doc = get_document_by_id(doc_id)
        if doc:
            return (
                doc[3] or "",  # jd
                doc[2] or "",  # resume
                doc[4] or "",  # summary
                doc[1] or "",  # name
                doc[0],  # selected_id
                doc[1],  # original_name
                gr.Button(interactive=True),  # enable delete button
                gr.Button(interactive=True),  # enable clear form button
            )
    except Exception as e:
        print(f"Error fetching document {doc_id}: {e}")

    return "", "", "", "", None, None, gr.Button(interactive=False), gr.Button(interactive=False)


def submit_or_update(
    selected_id: Optional[int],
    original_name: Optional[str],
    name: str,
    resume: str,
    jd: str,
    summary: str,
    search_term: str,
) -> Tuple[str, str, str, str, None, None, gr.Dataframe, gr.Button, gr.Button]:
    """
    Create new or update existing document.

    Args:
        selected_id: ID of document being edited (None for new)
        original_name: Original name (for update validation)
        name: Document name
        resume: Resume text
        jd: Job description text
        summary: Summary text
        search_term: Current search filter

    Returns:
        Tuple of (jd, resume, summary, name, None, None, dataframe, delete_button, clear_form_button)
    """
    # Validate name
    if not name or not name.strip():
        gr.Warning("Name is required")
        form_has_content = not is_form_empty(jd, resume, summary, name)
        return (
            jd,
            resume,
            summary,
            name,
            selected_id,
            original_name,
            gr.Dataframe(value=load_documents(search_term)),
            gr.Button(interactive=bool(selected_id)),
            gr.Button(interactive=form_has_content),
        )

    try:
        if selected_id is None:
            # Create new document
            success, message, doc_id = create_document(name, resume, jd, summary)
            if success:
                gr.Info(message)
                # Clear form and refresh dataframe
                return (
                    "",
                    "",
                    "",
                    "",
                    None,
                    None,
                    gr.Dataframe(value=load_documents(search_term)),
                    gr.Button(interactive=False),
                    gr.Button(interactive=False),
                )
            else:
                gr.Warning(message)
                form_has_content = not is_form_empty(jd, resume, summary, name)
                return (
                    jd,
                    resume,
                    summary,
                    name,
                    selected_id,
                    original_name,
                    gr.Dataframe(value=load_documents(search_term)),
                    gr.Button(interactive=bool(selected_id)),
                    gr.Button(interactive=form_has_content),
                )
        else:
            # Update existing document
            success, message = update_document(selected_id, name, resume, jd, summary)
            if success:
                gr.Info(message)
                # Clear form and refresh dataframe
                return (
                    "",
                    "",
                    "",
                    "",
                    None,
                    None,
                    gr.Dataframe(value=load_documents(search_term)),
                    gr.Button(interactive=False),
                    gr.Button(interactive=False),
                )
            else:
                gr.Warning(message)
                form_has_content = not is_form_empty(jd, resume, summary, name)
                return (
                    jd,
                    resume,
                    summary,
                    name,
                    selected_id,
                    original_name,
                    gr.Dataframe(value=load_documents(search_term)),
                    gr.Button(interactive=bool(selected_id)),
                    gr.Button(interactive=form_has_content),
                )
    except Exception as e:
        gr.Error(f"Database error: {str(e)}")
        form_has_content = not is_form_empty(jd, resume, summary, name)
        return (
            jd,
            resume,
            summary,
            name,
            selected_id,
            original_name,
            gr.Dataframe(value=load_documents(search_term)),
            gr.Button(interactive=bool(selected_id)),
            gr.Button(interactive=form_has_content),
        )


def delete_record(
    selected_id: Optional[int], search_term: str
) -> Tuple[str, str, str, str, None, None, gr.Dataframe, gr.Button, gr.Button]:
    """
    Soft delete selected document.

    Args:
        selected_id: ID of document to delete
        search_term: Current search filter

    Returns:
        Tuple of (empty fields, None, None, dataframe, delete_button, clear_form_button)
    """
    if selected_id is None:
        gr.Warning("No document selected")
        return (
            "",
            "",
            "",
            "",
            None,
            None,
            gr.Dataframe(value=load_documents(search_term)),
            gr.Button(interactive=False),
            gr.Button(interactive=False),
        )

    try:
        success, message = soft_delete_document(selected_id)
        if success:
            gr.Info(message)
        else:
            gr.Error(message)

        # Clear form and refresh dataframe
        return (
            "",
            "",
            "",
            "",
            None,
            None,
            gr.Dataframe(value=load_documents(search_term)),
            gr.Button(interactive=False),
            gr.Button(interactive=False),
        )
    except Exception as e:
        gr.Error(f"Database error: {str(e)}")
        return (
            "",
            "",
            "",
            "",
            None,
            None,
            gr.Dataframe(value=load_documents(search_term)),
            gr.Button(interactive=False),
            gr.Button(interactive=False),
        )


def clear_form(
    search_term: str,
) -> Tuple[str, str, str, str, None, None, gr.Dataframe, gr.Button, gr.Button]:
    """
    Reset form to initial state.

    Args:
        search_term: Current search filter

    Returns:
        Tuple of (empty fields, None, None, current dataframe, delete_button, clear_form_button)
    """
    return (
        "",
        "",
        "",
        "",
        None,
        None,
        gr.Dataframe(value=load_documents(search_term)),
        gr.Button(interactive=False),
        gr.Button(interactive=False),
    )


def on_form_change(
    jd: str, resume: str, summary: str, name: str
) -> gr.Button:
    """
    Update clear form button state based on form content.

    Args:
        jd: Job description text
        resume: Resume text
        summary: Summary text
        name: Name text

    Returns:
        Updated clear form button
    """
    form_has_content = not is_form_empty(jd, resume, summary, name)
    return gr.Button(interactive=form_has_content)


def create_ui() -> gr.Blocks:
    """
    Create and configure the Gradio UI.

    Returns:
        Gradio Blocks interface
    """
    # Check database connectivity
    if not initialize_database():
        print("Warning: Database not initialized. Please run migration.")

    with gr.Blocks(title="Documents Management") as demo:
        gr.Markdown("# Documents Management System")
        gr.Markdown(
            "Manage job descriptions, resumes, and summaries with search and CRUD operations."
        )

        # State variables
        selected_row_id = gr.State(None)
        original_name = gr.State(None)

        # Row 1: Document Content
        with gr.Row():
            jd_textbox = gr.Textbox(
                label="Job Description",
                lines=15,
                placeholder="Paste job description here (avg 8192 chars)...",
                max_lines=20,
                scale=1,
            )
            resume_textbox = gr.Textbox(
                label="Resume",
                lines=15,
                placeholder="Paste resume here (avg 8192 chars)...",
                max_lines=20,
                scale=1,
            )

        # Row 2: Metadata
        with gr.Row():
            summary_textbox = gr.Textbox(
                label="Summary", lines=3, placeholder="Brief summary...", scale=3
            )
            name_textbox = gr.Textbox(
                label="Name", lines=1, placeholder="Unique collection name...", scale=1
            )

        # Row 3: Actions
        with gr.Row():
            submit_button = gr.Button("Submit or Update", variant="primary", scale=1)
            delete_button = gr.Button(
                "Delete", variant="stop", interactive=False, scale=1
            )
            clear_form_button = gr.Button("Clear Form", variant="secondary", interactive=False, scale=1)

        # Horizontal rule separator
        gr.Markdown("---")

        # Row 4: Search (above table)
        with gr.Row():
            search_textbox = gr.Textbox(
                label="Search by Name",
                placeholder="Type to filter documents...",
                scale=3,
            )
            clear_search_button = gr.Button("Clear Search", scale=1)

        # Row 5: Data Display
        dataframe = gr.Dataframe(
            headers=["ID", "Name", "Resume (preview)", "JD (preview)", "Summary", "Updated"],
            datatype=["number", "str", "str", "str", "str", "str"],
            value=load_documents(""),
            interactive=False,
            wrap=True,
        )

        # Event Handlers

        # Search functionality
        search_textbox.change(
            fn=on_search, inputs=[search_textbox], outputs=[dataframe]
        )

        # Clear search
        clear_search_button.click(
            fn=on_clear_search, inputs=[], outputs=[search_textbox, dataframe]
        )

        # Row selection
        dataframe.select(
            fn=on_row_select,
            inputs=[dataframe],
            outputs=[
                jd_textbox,
                resume_textbox,
                summary_textbox,
                name_textbox,
                selected_row_id,
                original_name,
                delete_button,
                clear_form_button,
            ],
        )

        # Submit or Update
        submit_button.click(
            fn=submit_or_update,
            inputs=[
                selected_row_id,
                original_name,
                name_textbox,
                resume_textbox,
                jd_textbox,
                summary_textbox,
                search_textbox,
            ],
            outputs=[
                jd_textbox,
                resume_textbox,
                summary_textbox,
                name_textbox,
                selected_row_id,
                original_name,
                dataframe,
                delete_button,
                clear_form_button,
            ],
        )

        # Delete
        delete_button.click(
            fn=delete_record,
            inputs=[selected_row_id, search_textbox],
            outputs=[
                jd_textbox,
                resume_textbox,
                summary_textbox,
                name_textbox,
                selected_row_id,
                original_name,
                dataframe,
                delete_button,
                clear_form_button,
            ],
        )

        # Clear form
        clear_form_button.click(
            fn=clear_form,
            inputs=[search_textbox],
            outputs=[
                jd_textbox,
                resume_textbox,
                summary_textbox,
                name_textbox,
                selected_row_id,
                original_name,
                dataframe,
                delete_button,
                clear_form_button,
            ],
        )

        # Form field change handlers - enable/disable clear form button
        for field in [jd_textbox, resume_textbox, summary_textbox, name_textbox]:
            field.change(
                fn=on_form_change,
                inputs=[jd_textbox, resume_textbox, summary_textbox, name_textbox],
                outputs=[clear_form_button],
            )

    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)

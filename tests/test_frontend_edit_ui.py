from pathlib import Path


def _read_static_file(name: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / "app" / "static" / name).read_text(encoding="utf-8")


def test_edit_dialog_is_present_and_described_by_status() -> None:
    html = _read_static_file("index.html")

    assert 'id="edit-book-dialog"' in html
    assert 'id="edit-book-form"' in html
    assert 'aria-describedby="edit-status"' in html
    assert 'id="edit-status"' in html


def test_edit_flow_uses_put_and_handles_required_status_states() -> None:
    javascript = _read_static_file("app.js")

    assert "data-edit-book-id" in javascript
    assert 'method: "PUT"' in javascript
    assert 'setEditStatus("Working...", "working")' in javascript
    assert 'successMessage: "Book updated successfully."' in javascript
    assert 'setEditStatus("Validation failed. Check all required fields.", "validation")' in javascript
    assert 'setEditStatus("Duplicate ISBN. Please use a unique ISBN.", "duplicate")' in javascript
    assert 'setEditStatus("Could not update book because it was not found.", "error")' in javascript
    assert 'setEditStatus("Unexpected error while updating book.", "error")' in javascript
    assert 'setEditStatus("Network error while updating book.", "error")' in javascript


def test_edit_load_flow_prefills_book_and_uses_dialog_status_for_errors() -> None:
    javascript = _read_static_file("app.js")
    open_edit_function = javascript.split("async function openEditBookForm(bookId) {", 1)[1].split(
        "\n}\n\nfunction toggleBookListButtons",
        1,
    )[0]

    assert "editDialog.showModal();" in open_edit_function
    assert "const response = await fetch(`/api/books/${bookId}`);" in open_edit_function
    assert "populateEditForm(book);" in open_edit_function
    assert "setEditStatus(\"Could not load the selected book for editing.\", \"error\")" in open_edit_function
    assert "setSearchStatus(" not in open_edit_function

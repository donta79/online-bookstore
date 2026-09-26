const form = document.getElementById("add-book-form");
const statusElement = document.getElementById("status");
const submitButton = document.getElementById("submit-button");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-query");
const searchButton = document.getElementById("search-button");
const searchStatusElement = document.getElementById("search-status");
const agentForm = document.getElementById("agent-form");
const agentQuestionInput = document.getElementById("agent-question");
const askAgentButton = document.getElementById("ask-agent-button");
const agentProgress = document.getElementById("agent-progress");
const agentStatusElement = document.getElementById("agent-status");
const agentAnswerElement = document.getElementById("agent-answer");
const agentResultsElement = document.getElementById("agent-results");
const bookList = document.getElementById("book-list");
const detailsDialog = document.getElementById("book-details-dialog");
const editDialog = document.getElementById("edit-book-dialog");
const editForm = document.getElementById("edit-book-form");
const editStatusElement = document.getElementById("edit-status");
const editSaveButton = document.getElementById("edit-save-button");
const editFields = {
  id: document.getElementById("edit-book-id"),
  title: document.getElementById("edit-title"),
  author: document.getElementById("edit-author"),
  isbn: document.getElementById("edit-isbn"),
  description: document.getElementById("edit-description"),
  availability: document.getElementById("edit-availability"),
};
const summarizeButton = document.getElementById("summarize-button");
const summaryStatusElement = document.getElementById("summary-status");
const summaryTextElement = document.getElementById("summary-text");
const detailsFields = {
  id: document.getElementById("details-id"),
  title: document.getElementById("details-title"),
  author: document.getElementById("details-author"),
  isbn: document.getElementById("details-isbn"),
  description: document.getElementById("details-description"),
  availability: document.getElementById("details-availability"),
};
let selectedDescription = "";

function setStatus(message, stateClass) {
  statusElement.textContent = message;
  statusElement.className = stateClass;
}

function setSearchStatus(message, stateClass) {
  searchStatusElement.textContent = message;
  searchStatusElement.className = stateClass;
}

function setEditStatus(message, stateClass) {
  editStatusElement.textContent = message;
  editStatusElement.className = stateClass;
}

function setAgentStatus(message, stateClass) {
  agentStatusElement.textContent = message;
  agentStatusElement.className = stateClass;
}

function setAgentProgress(visible) {
  agentProgress.classList.toggle("visible", visible);
}

function renderAgentResults(results) {
  agentResultsElement.innerHTML = "";
  for (const book of results) {
    const item = document.createElement("li");
    item.className = "book-card";

    const title = document.createElement("h3");
    title.textContent = book.title;

    const author = document.createElement("p");
    const authorLabel = document.createElement("strong");
    authorLabel.textContent = "Author:";
    author.appendChild(authorLabel);
    author.append(` ${book.author}`);

    const availability = document.createElement("p");
    const availabilityLabel = document.createElement("strong");
    availabilityLabel.textContent = "Availability:";
    availability.appendChild(availabilityLabel);
    availability.append(` ${book.availability ? "In stock" : "Out of stock"}`);

    item.appendChild(title);
    item.appendChild(author);
    item.appendChild(availability);
    agentResultsElement.appendChild(item);
  }
}

function renderBooks(books) {
  bookList.innerHTML = "";
  for (const book of books) {
    const item = document.createElement("li");
    item.className = "book-card";

    const title = document.createElement("h3");
    title.textContent = book.title;

    const author = document.createElement("p");
    const authorLabel = document.createElement("strong");
    authorLabel.textContent = "Author:";
    author.appendChild(authorLabel);
    author.append(` ${book.author}`);

    const availability = document.createElement("p");
    const availabilityLabel = document.createElement("strong");
    availabilityLabel.textContent = "Availability:";
    availability.appendChild(availabilityLabel);
    availability.append(` ${book.availability ? "In stock" : "Out of stock"}`);

    const actions = document.createElement("div");
    actions.className = "book-card-actions";

    const detailsButton = document.createElement("button");
    detailsButton.type = "button";
    detailsButton.dataset.viewBookId = String(book.id);
    detailsButton.textContent = "View details";

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "delete-button";
    deleteButton.dataset.deleteBookId = String(book.id);
    deleteButton.dataset.bookTitle = book.title;
    deleteButton.textContent = "Delete book";

    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.dataset.editBookId = String(book.id);
    editButton.textContent = "Edit book";

    actions.appendChild(detailsButton);
    actions.appendChild(editButton);
    actions.appendChild(deleteButton);
    item.appendChild(title);
    item.appendChild(author);
    item.appendChild(availability);
    item.appendChild(actions);
    bookList.appendChild(item);
  }
}

function populateBookDetails(book) {
  detailsFields.id.textContent = String(book.id);
  detailsFields.title.textContent = book.title;
  detailsFields.author.textContent = book.author;
  detailsFields.isbn.textContent = book.isbn;
  detailsFields.description.textContent = book.description;
  detailsFields.availability.textContent = book.availability ? "In stock" : "Out of stock";
  selectedDescription = book.description;
  resetSummary();
}

function setSummaryStatus(message, stateClass) {
  summaryStatusElement.textContent = message;
  summaryStatusElement.className = stateClass;
}

function resetSummary() {
  summaryTextElement.textContent = "";
  setSummaryStatus("", "");
}

async function openBookDetails(bookId) {
  try {
    const response = await fetch(`/api/books/${bookId}`);
    if (!response.ok) {
      throw new Error("Failed to fetch book details");
    }

    const book = await response.json();
    populateBookDetails(book);
    detailsDialog.showModal();
  } catch (error) {
    setSearchStatus("Could not load book details. Please try again.", "duplicate");
  }
}

async function summarizeSelectedBook() {
  if (!selectedDescription) {
    setSummaryStatus("No description is available to summarize.", "validation");
    return;
  }

  setSummaryStatus("Summarizing...", "working");
  summaryTextElement.textContent = "";
  summarizeButton.disabled = true;

  try {
    const response = await fetch("/api/ai/summaries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: selectedDescription }),
    });

    if (response.ok) {
      const body = await response.json();
      summaryTextElement.textContent = body.summary;
      setSummaryStatus("Summary ready.", "success");
      return;
    }

    if (response.status === 503) {
      setSummaryStatus("Summary is unavailable right now. Please try again later.", "duplicate");
      return;
    }

    setSummaryStatus("Could not summarize this book. Please try again.", "duplicate");
  } catch (error) {
    setSummaryStatus("Could not summarize this book. Please try again.", "duplicate");
  } finally {
    summarizeButton.disabled = false;
  }
}

function populateEditForm(book) {
  editFields.id.value = String(book.id);
  editFields.title.value = book.title;
  editFields.author.value = book.author;
  editFields.isbn.value = book.isbn;
  editFields.description.value = book.description;
  editFields.availability.checked = book.availability;
}

async function openEditBookForm(bookId) {
  editFields.id.value = String(bookId);
  editFields.title.value = "";
  editFields.author.value = "";
  editFields.isbn.value = "";
  editFields.description.value = "";
  editFields.availability.checked = false;
  setEditStatus("Loading book...", "working");
  editSaveButton.disabled = true;
  editDialog.showModal();
  try {
    const response = await fetch(`/api/books/${bookId}`);
    if (!response.ok) {
      throw new Error("Failed to fetch book for edit");
    }

    const book = await response.json();
    populateEditForm(book);
    setEditStatus("", "");
    editSaveButton.disabled = false;
  } catch (error) {
    setEditStatus("Could not load the selected book for editing.", "error");
  }
}

function toggleBookListButtons(disabled) {
  for (const button of bookList.querySelectorAll("button")) {
    button.disabled = disabled;
  }
}

async function refreshBooks(query = "", options = {}) {
  const { successMessage = "" } = options;
  setSearchStatus("Loading books...", "working");
  searchButton.disabled = true;

  try {
    const params = new URLSearchParams();
    if (query.trim()) {
      params.set("q", query);
    }

    const url = params.toString() ? `/api/books?${params.toString()}` : "/api/books";
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Failed to fetch books");
    }

    const books = await response.json();
    renderBooks(books);

    if (books.length === 0) {
      if (!query.trim()) {
        setSearchStatus("Catalogue is empty.", "no-results");
        return;
      }

      setSearchStatus("No books found for that search.", "no-results");
      return;
    }

    setSearchStatus(successMessage || `Showing ${books.length} book(s).`, "success");
  } catch (error) {
    setSearchStatus("Could not load books. Please try again.", "duplicate");
  } finally {
    searchButton.disabled = false;
  }
}

async function deleteBook(bookId, title) {
  const confirmed = window.confirm(`Delete "${title}" from the catalogue?`);
  if (!confirmed) {
    return;
  }

  setSearchStatus("Deleting book...", "working");
  toggleBookListButtons(true);

  try {
    const response = await fetch(`/api/books/${bookId}`, {
      method: "DELETE",
    });

    if (response.status === 204) {
      if (detailsDialog.open && detailsFields.id.textContent === String(bookId)) {
        detailsDialog.close();
      }

      await refreshBooks(searchInput.value, { successMessage: "Book deleted successfully." });
      return;
    }

    if (response.status === 404) {
      setSearchStatus("Could not delete book because it was not found.", "duplicate");
      return;
    }

    setSearchStatus("Could not delete book. Please try again.", "duplicate");
  } catch (error) {
    setSearchStatus("Could not delete book. Please try again.", "duplicate");
  } finally {
    toggleBookListButtons(false);
  }
}

async function askCatalogueAgent(question) {
  setAgentStatus("Agent is working...", "working");
  setAgentProgress(true);
  agentAnswerElement.textContent = "";
  askAgentButton.disabled = true;

  try {
    const response = await fetch("/api/agent/catalog", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (response.ok) {
      const body = await response.json();
      setAgentStatus("Agent answer ready.", "success");
      agentAnswerElement.textContent = body.answer;
      renderAgentResults(body.results);
      if (body.results.length === 0) {
        setAgentStatus("No matching books found by the agent.", "no-results");
      }
      return;
    }

    if (response.status === 503) {
      setAgentStatus("Catalogue agent is unavailable right now. Please try again later.", "duplicate");
      renderAgentResults([]);
      return;
    }

    setAgentStatus("Could not get an agent answer. Please try again.", "duplicate");
    renderAgentResults([]);
  } catch (error) {
    setAgentStatus("Could not get an agent answer. Please try again.", "duplicate");
    renderAgentResults([]);
  } finally {
    askAgentButton.disabled = false;
    setAgentProgress(false);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    title: document.getElementById("title").value,
    author: document.getElementById("author").value,
    isbn: document.getElementById("isbn").value,
    description: document.getElementById("description").value,
    availability: document.getElementById("availability").checked,
  };

  setStatus("Working...", "working");
  submitButton.disabled = true;

  try {
    const response = await fetch("/api/books", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.status === 201) {
      form.reset();
      document.getElementById("availability").checked = true;
      setStatus("Book added successfully.", "success");
      await refreshBooks(searchInput.value);
      return;
    }

    if (response.status === 422) {
      setStatus("Validation failed. Check all required fields.", "validation");
      return;
    }

    if (response.status === 409) {
      setStatus("Duplicate ISBN. Please use a unique ISBN.", "duplicate");
      return;
    }

    setStatus("Unexpected error while adding book.", "duplicate");
  } catch (error) {
    setStatus("Network error while adding book.", "duplicate");
  } finally {
    submitButton.disabled = false;
  }
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await refreshBooks(searchInput.value);
});

agentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await askCatalogueAgent(agentQuestionInput.value);
});

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const bookId = editFields.id.value;
  const payload = {
    title: editFields.title.value,
    author: editFields.author.value,
    isbn: editFields.isbn.value,
    description: editFields.description.value,
    availability: editFields.availability.checked,
  };

  setEditStatus("Working...", "working");
  editSaveButton.disabled = true;

  try {
    const response = await fetch(`/api/books/${bookId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.status === 200) {
      editDialog.close();
      await refreshBooks(searchInput.value, { successMessage: "Book updated successfully." });
      return;
    }

    if (response.status === 422) {
      setEditStatus("Validation failed. Check all required fields.", "validation");
      return;
    }

    if (response.status === 409) {
      setEditStatus("Duplicate ISBN. Please use a unique ISBN.", "duplicate");
      return;
    }

    if (response.status === 404) {
      setEditStatus("Could not update book because it was not found.", "error");
      return;
    }

    setEditStatus("Unexpected error while updating book.", "error");
  } catch (error) {
    setEditStatus("Network error while updating book.", "error");
  } finally {
    editSaveButton.disabled = false;
  }
});

bookList.addEventListener("click", async (event) => {
  const editButton = event.target.closest("[data-edit-book-id]");
  if (editButton) {
    await openEditBookForm(editButton.dataset.editBookId);
    return;
  }

  const deleteButton = event.target.closest("[data-delete-book-id]");
  if (deleteButton) {
    await deleteBook(deleteButton.dataset.deleteBookId, deleteButton.dataset.bookTitle);
    return;
  }

  const detailsButton = event.target.closest("[data-view-book-id]");
  if (!detailsButton) {
    return;
  }

  await openBookDetails(detailsButton.dataset.viewBookId);
});

summarizeButton.addEventListener("click", async () => {
  await summarizeSelectedBook();
});

refreshBooks("");

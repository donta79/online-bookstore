const form = document.getElementById("add-book-form");
const statusElement = document.getElementById("status");
const submitButton = document.getElementById("submit-button");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-query");
const searchButton = document.getElementById("search-button");
const searchStatusElement = document.getElementById("search-status");
const bookList = document.getElementById("book-list");
const detailsDialog = document.getElementById("book-details-dialog");
const detailsFields = {
  id: document.getElementById("details-id"),
  title: document.getElementById("details-title"),
  author: document.getElementById("details-author"),
  isbn: document.getElementById("details-isbn"),
  description: document.getElementById("details-description"),
  availability: document.getElementById("details-availability"),
};

function setStatus(message, stateClass) {
  statusElement.textContent = message;
  statusElement.className = stateClass;
}

function setSearchStatus(message, stateClass) {
  searchStatusElement.textContent = message;
  searchStatusElement.className = stateClass;
}

function renderBooks(books) {
  bookList.innerHTML = "";
  for (const book of books) {
    const item = document.createElement("li");
    item.className = "book-card";
    item.innerHTML = `
      <h3>${book.title}</h3>
      <p><strong>Author:</strong> ${book.author}</p>
      <p><strong>Availability:</strong> ${book.availability ? "In stock" : "Out of stock"}</p>
      <button type="button" data-book-id="${book.id}">View details</button>
    `;
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

async function refreshBooks(query = "") {
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
      setSearchStatus("No books found for that search.", "no-results");
      return;
    }

    setSearchStatus(`Showing ${books.length} book(s).`, "success");
  } catch (error) {
    setSearchStatus("Could not load books. Please try again.", "duplicate");
  } finally {
    searchButton.disabled = false;
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

bookList.addEventListener("click", async (event) => {
  const detailsButton = event.target.closest("[data-book-id]");
  if (!detailsButton) {
    return;
  }

  await openBookDetails(detailsButton.dataset.bookId);
});

refreshBooks("");

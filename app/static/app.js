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
const agentStatusElement = document.getElementById("agent-status");
const agentAnswerElement = document.getElementById("agent-answer");
const agentResultsElement = document.getElementById("agent-results");
const bookList = document.getElementById("book-list");
const detailsDialog = document.getElementById("book-details-dialog");
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

function setAgentStatus(message, stateClass) {
  agentStatusElement.textContent = message;
  agentStatusElement.className = stateClass;
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

async function refreshBooks(query = "") {
  setSearchStatus("Loading books...", "working");
  searchButton.disabled = true;

  try {
    const params = new URLSearchParams();
    if (query.trim()) {
      params.set("q", query);
    }

    async function askCatalogueAgent(question) {
      setAgentStatus("Agent is working...", "working");
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
      }
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

agentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await askCatalogueAgent(agentQuestionInput.value);
});

bookList.addEventListener("click", async (event) => {
  const detailsButton = event.target.closest("[data-book-id]");
  if (!detailsButton) {
    return;
  }

  await openBookDetails(detailsButton.dataset.bookId);
});

summarizeButton.addEventListener("click", async () => {
  await summarizeSelectedBook();
});

refreshBooks("");

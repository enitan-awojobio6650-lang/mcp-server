"""
Library Management System MCP Server

Exposes:
  - 4 tools: search_books, check_availability, borrow_book, return_book
  - 2 resources: library://info/hours (static), member://{member_id}/history (template)
  - 1 prompt: recommend_books(genre, mood)
"""

from typing import Optional
from fastmcp import FastMCP

mcp = FastMCP("Library Server")

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

BOOKS: dict[str, dict] = {
    "9780143127550": {
        "title": "The Alchemist",
        "author": "Paulo Coelho",
        "isbn": "9780143127550",
        "available_copies": 3,
    },
    "9780451524935": {
        "title": "Things Fall Apart",
        "author": "Chinua Achebe",
        "isbn": "9780451524935",
        "available_copies": 2,
    },
    "9780756404741": {
        "title": "The Way of Kings",
        "author": "Brandon Sanderson",
        "isbn": "9780756404741",
        "available_copies": 0,
    },
    "9780062316097": {
        "title": "Sapiens",
        "author": "Yuval Noah Harari",
        "isbn": "9780062316097",
        "available_copies": 4,
    },
    "9780441172719": {
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "9780441172719",
        "available_copies": 1,
    },
    "9780553380163": {
        "title": "A Brief History of Time",
        "author": "Stephen Hawking",
        "isbn": "9780553380163",
        "available_copies": 2,
    },
    "9780345391803": {
        "title": "The Hitchhiker's Guide to the Galaxy",
        "author": "Douglas Adams",
        "isbn": "9780345391803",
        "available_copies": 5,
    },
    "9780618260300": {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "isbn": "9780618260300",
        "available_copies": 0,
    },
}

# member_id -> list of {"isbn": ..., "title": ...} previously borrowed
MEMBER_HISTORY: dict[str, list[dict]] = {
    "M001": [
        {"isbn": "9780143127550", "title": "The Alchemist"},
        {"isbn": "9780441172719", "title": "Dune"},
    ],
    "M002": [
        {"isbn": "9780451524935", "title": "Things Fall Apart"},
    ],
}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool
def search_books(query: str) -> list[dict]:
    """
    Search the library catalog by book title or author name (case-insensitive,
    partial match allowed).

    Use this tool when the user wants to find books about a topic, by an
    author, or with a specific title, and you don't already know the ISBN.

    Args:
        query: A search string to match against book titles and authors.

    Returns:
        A list of matching book records (title, author, isbn, available_copies).
        Empty list if nothing matches.
    """
    q = query.lower().strip()
    results = [
        book
        for book in BOOKS.values()
        if q in book["title"].lower() or q in book["author"].lower()
    ]
    return results


@mcp.tool
def check_availability(isbn: str) -> str:
    """
    Check how many copies of a specific book are currently available to borrow.

    Use this tool when you already have a book's ISBN (e.g. from search_books)
    and need to know if it can be borrowed right now.

    Args:
        isbn: The ISBN of the book to check.

    Returns:
        A human-readable string describing availability, or an error string
        if the ISBN is not found in the catalog.
    """
    book = BOOKS.get(isbn)
    if book is None:
        return f"Error: no book found with ISBN {isbn}."
    return f"'{book['title']}' has {book['available_copies']} copy(ies) available."


@mcp.tool
def borrow_book(isbn: str, member_id: str) -> str:
    """
    Borrow a book on behalf of a library member, decreasing its available
    copy count by one and recording it in the member's borrow history.

    Use this tool once the user has decided to borrow a specific book
    (identified by ISBN) and you know their member ID.

    Args:
        isbn: The ISBN of the book to borrow.
        member_id: The ID of the member borrowing the book.

    Returns:
        A success message string, or an error string if the book doesn't
        exist or has no copies available. Never raises an exception.
    """
    book = BOOKS.get(isbn)
    if book is None:
        return f"Error: no book found with ISBN {isbn}."
    if book["available_copies"] <= 0:
        return f"Error: '{book['title']}' has no copies available to borrow."

    book["available_copies"] -= 1
    MEMBER_HISTORY.setdefault(member_id, []).append(
        {"isbn": isbn, "title": book["title"]}
    )
    return (
        f"Success: '{book['title']}' borrowed by member {member_id}. "
        f"{book['available_copies']} copy(ies) remaining."
    )


@mcp.tool
def return_book(isbn: str, member_id: str) -> str:
    """
    Return a previously borrowed book on behalf of a library member,
    increasing its available copy count by one.

    Use this tool when the user says they want to return a book they
    borrowed.

    Args:
        isbn: The ISBN of the book being returned.
        member_id: The ID of the member returning the book.

    Returns:
        A success message string, or an error string if the book doesn't
        exist. Never raises an exception.
    """
    book = BOOKS.get(isbn)
    if book is None:
        return f"Error: no book found with ISBN {isbn}."

    book["available_copies"] += 1
    return (
        f"Success: '{book['title']}' returned by member {member_id}. "
        f"{book['available_copies']} copy(ies) now available."
    )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("library://info/hours")
def library_hours() -> str:
    """Static resource: the library's operating hours."""
    return (
        "Library Hours:\n"
        "Monday - Friday: 8:00 AM - 8:00 PM\n"
        "Saturday: 9:00 AM - 5:00 PM\n"
        "Sunday: Closed"
    )


@mcp.resource("member://{member_id}/history")
def member_history(member_id: str) -> list[dict]:
    """Dynamic resource template: a specific member's borrow history."""
    return MEMBER_HISTORY.get(member_id, [])


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

@mcp.prompt
def recommend_books(genre: str, mood: str) -> str:
    """Generate a prompt template asking for book recommendations by genre and mood."""
    return (
        f"Recommend 3 books in the '{genre}' genre that would suit someone "
        f"currently in a '{mood}' mood. For each book, give the title, author, "
        f"and a one-sentence reason it fits the mood."
    )


if __name__ == "__main__":
    mcp.run()
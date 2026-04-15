# DeKUT Library Management System

NOTE: Certain aspects of the application specifically the templates are built in conjunction with an AI Agentic System (Claude Code).You are thereby requested to open a pull request if you encounter an issue or contact the developer at [issues.allan7ycrx.org](https://issues.allan7ycrx.org)

**Dedan Kimathi University of Technology**  
📍 Private Bag, Dedan Kimathi University, Nyeri, Kenya  
🌐 [www.dkut.ac.ke](https://www.dkut.ac.ke)

---

## Overview

A Flask-based Library Management System built for DeKUT.  
Uses Python + Flask + AivenPostgreSQL + Jinja2 templates + Bootstrap 5.

---

## Features

### Librarian
- Login / Logout
- Add, Edit, Delete books
- Register student members
- Issue books to students (with due-date tracking)
- Process book returns (auto fine calculation at KSH 10/day)
- View all loan records (active / overdue / returned)
- Reports: top borrowed, overdue list, genre stats, fine summary

### Student
- Login / Logout
- Browse & search the book catalogue
- View current loans and due dates
- View borrowing history and fines

---

## Quick Start

```bash
# 1. We are using UV to manage the virtual Environments and dependencies.Its first as it is built on Rust.
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync --frozen

# 3. Run (using Gunicorn for production
uv run gunicorn -w 2 --timeout 120 -b 0.0.0.0:$PORT main:app
```

Open `http://localhost:$PORT` in your browser.

---
# Authentication and Authorization

Students are registered by the librarian through the Members section.

---

## Project Structure

```
lms/
├── main.py                   # Main Flask app + all routes
├── model.py
├── pyproject.toml
├── static/
│   └── css/
│       └── style.css        # DeKUT green/gold theme
└── templates/
    ├── base.html            # Navbar + footer layout
    ├── login.html
    ├── dashboard.html
    ├── books.html
    ├── add_book.html
    ├── edit_book.html
    ├── members.html
    ├── register_member.html
    ├── loans.html
    ├── issue_book.html
    ├── my_loans.html        # Student view
    └── reports.html
```

---

## Fine Calculation

- Fine rate: **KSH 10 per overdue day**
- Fines are automatically calculated when a book is returned late
- Librarian can mark fines as paid from the Reports page

---

## Database Schema

| Table    | Key Fields                                          |
|----------|-----------------------------------------------------|
| users    | id, username, password, role, full_name, email, phone |
| books    | id, title, author, isbn, genre, copies_total, copies_available |
| loans    | id, book_id, student_id, issue_date, due_date, return_date, status |
| fines    | id, loan_id, amount, paid_status, paid_date         |

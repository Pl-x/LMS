# DeKUT Library Management System

**Dedan Kimathi University of Technology**  
📍 Private Bag, Dedan Kimathi University, Nyeri, Kenya  
🌐 [www.dkut.ac.ke](https://www.dkut.ac.ke)

---

## Overview

A Flask-based Library Management System built for DeKUT.  
Uses Python + Flask + SQLite + Jinja2 templates + Bootstrap 5.

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
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
```

Open `http://localhost:5000` in your browser.

---

## Default Credentials

| Role       | Username    | Password   |
|------------|-------------|------------|
| Librarian  | `librarian` | `admin123` |

Students are registered by the librarian through the Members section.

---

## Project Structure

```
dkut_lms/
├── app.py                   # Main Flask app + all routes
├── lms.db                   # SQLite database (auto-created)
├── requirements.txt
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

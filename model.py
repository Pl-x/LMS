import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('librarian','student')),
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            genre TEXT,
            copies_total INTEGER DEFAULT 1,
            copies_available INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id SERIAL PRIMARY KEY,
            book_id INTEGER NOT NULL REFERENCES books(id),
            student_id INTEGER NOT NULL REFERENCES users(id),
            issued_by INTEGER NOT NULL REFERENCES users(id),
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            status TEXT DEFAULT 'active' CHECK(status IN ('active','returned','overdue'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            id SERIAL PRIMARY KEY,
            loan_id INTEGER NOT NULL REFERENCES loans(id),
            amount REAL NOT NULL,
            paid_status TEXT DEFAULT 'unpaid' CHECK(paid_status IN ('unpaid','paid')),
            paid_date DATE
        )
    ''')

    # Sample books
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        sample_books = [
            ('Introduction to Algorithms', 'Cormen et al.', '978-0262033848', 'Computer Science', 3, 3),
            ('Database System Concepts', 'Silberschatz', '978-0073523323', 'Computer Science', 2, 2),
            ('Engineering Mathematics', 'K.A. Stroud', '978-1137031204', 'Mathematics', 4, 4),
            ('Computer Networks', 'Andrew Tanenbaum', '978-0132126953', 'Computer Science', 2, 2),
            ('Operating Systems', 'William Stallings', '978-0134670959', 'Computer Science', 3, 3),
            ('Calculus', 'James Stewart', '978-1285740621', 'Mathematics', 5, 5),
            ('Digital Electronics', 'Floyd', '978-0132543033', 'Engineering', 2, 2),
            ('Physics for Scientists', 'Serway', '978-1133947271', 'Physics', 3, 3),
        ]
        c.executemany(
            "INSERT INTO books (title, author, isbn, genre, copies_total, copies_available) VALUES (%s,%s,%s,%s,%s,%s)",
            sample_books
        )

    conn.commit()
    c.close()
    conn.close()


#Users
def get_user_by_credentials(username, password):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = c.fetchone()
    c.close()
    conn.close()
    return user


def get_all_students(search=None):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if search:
        c.execute(
            "SELECT * FROM users WHERE role='student' AND (full_name ILIKE %s OR username ILIKE %s) ORDER BY full_name",
            (f'%{search}%', f'%{search}%')
        )
    else:
        c.execute("SELECT * FROM users WHERE role='student' ORDER BY full_name")
    members = c.fetchall()
    c.close()
    conn.close()
    return members


def create_student(username, password, full_name, email, phone):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password, role, full_name, email, phone) VALUES (%s,%s,'student',%s,%s,%s)",
        (username, password, full_name, email, phone)
    )
    conn.commit()
    c.close()
    conn.close()


#Books
def get_all_books(search=None, genre=None):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    if search:
        query += " AND (title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if genre:
        query += " AND genre = %s"
        params.append(genre)
    query += " ORDER BY title"
    c.execute(query, params)
    books = c.fetchall()
    c.close()
    conn.close()
    return books


def get_available_books():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM books WHERE copies_available > 0 ORDER BY title")
    books = c.fetchall()
    c.close()
    conn.close()
    return books


def get_all_genres():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT genre FROM books ORDER BY genre")
    genres = c.fetchall()
    c.close()
    conn.close()
    return genres


def add_book(title, author, isbn, genre, copies):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO books (title, author, isbn, genre, copies_total, copies_available) VALUES (%s,%s,%s,%s,%s,%s)",
        (title, author, isbn or None, genre, copies, copies)
    )
    conn.commit()
    c.close()
    conn.close()


def get_book_by_id(book_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = c.fetchone()
    c.close()
    conn.close()
    return book


def update_book(book_id, title, author, isbn, genre, copies_total):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE books
        SET title=%s, author=%s, isbn=%s, genre=%s,
            copies_total=%s,
            copies_available = copies_available + (%s - copies_total)
        WHERE id=%s
    ''', (title, author, isbn or None, genre, copies_total, copies_total, book_id))
    conn.commit()
    c.close()
    conn.close()


def delete_book(book_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id = %s", (book_id,))
    conn.commit()
    c.close()
    conn.close()


#Loans
def mark_overdue_loans():
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE loans SET status='overdue' WHERE status='active' AND due_date < CURRENT_DATE")
    conn.commit()
    c.close()
    conn.close()


def get_all_loans(status=None):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = '''
        SELECT l.id, b.title, b.isbn, u.full_name, u.username,
               l.issue_date, l.due_date, l.return_date, l.status
        FROM loans l
        JOIN books b ON l.book_id = b.id
        JOIN users u ON l.student_id = u.id
    '''
    if status:
        query += " WHERE l.status = %s"
        c.execute(query + " ORDER BY l.issue_date DESC", (status,))
    else:
        c.execute(query + " ORDER BY l.issue_date DESC")
    loans = c.fetchall()
    c.close()
    conn.close()
    return loans


def get_loan_by_id(loan_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM loans WHERE id = %s", (loan_id,))
    loan = c.fetchone()
    c.close()
    conn.close()
    return loan


def create_loan(book_id, student_id, issued_by, issue_date, due_date):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO loans (book_id, student_id, issued_by, issue_date, due_date) VALUES (%s,%s,%s,%s,%s)",
        (book_id, student_id, issued_by, issue_date, due_date)
    )
    c.execute("UPDATE books SET copies_available = copies_available - 1 WHERE id = %s", (book_id,))
    conn.commit()
    c.close()
    conn.close()


def return_loan(loan_id, book_id, return_date, fine_amount=None):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE loans SET status='returned', return_date=%s WHERE id=%s",
        (return_date, loan_id)
    )
    c.execute("UPDATE books SET copies_available = copies_available + 1 WHERE id=%s", (book_id,))
    if fine_amount:
        c.execute("INSERT INTO fines (loan_id, amount) VALUES (%s,%s)", (loan_id, fine_amount))
    conn.commit()
    c.close()
    conn.close()


def get_my_loans(student_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''
        SELECT l.id, b.title, b.author, l.issue_date, l.due_date,
               l.return_date, l.status,
               CASE WHEN l.return_date IS NULL AND l.due_date < CURRENT_DATE THEN 1 ELSE 0 END AS is_overdue
        FROM loans l
        JOIN books b ON l.book_id = b.id
        WHERE l.student_id = %s
        ORDER BY l.issue_date DESC
    ''', (student_id,))
    loans = c.fetchall()
    c.close()
    conn.close()
    return loans


def get_my_fines(student_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''
        SELECT f.amount, f.paid_status, b.title
        FROM fines f
        JOIN loans l ON f.loan_id = l.id
        JOIN books b ON l.book_id = b.id
        WHERE l.student_id = %s
    ''', (student_id,))
    fines = c.fetchall()
    c.close()
    conn.close()
    return fines


#Dashboard
def get_dashboard_stats():
    conn = get_db()
    c = conn.cursor()
    stats = {}
    c.execute("SELECT COUNT(*) FROM books")
    stats['total_books'] = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(copies_available), 0) FROM books")
    stats['available_books'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    stats['total_members'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM loans WHERE status='active'")
    stats['active_loans'] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM loans WHERE status='active' AND due_date < CURRENT_DATE")
    stats['overdue'] = c.fetchone()[0]
    c.close()
    conn.close()
    return stats


def get_recent_loans(limit=5):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''
        SELECT l.id, b.title, u.full_name, l.issue_date, l.due_date, l.status
        FROM loans l
        JOIN books b ON l.book_id = b.id
        JOIN users u ON l.student_id = u.id
        ORDER BY l.issue_date DESC
        LIMIT %s
    ''', (limit,))
    loans = c.fetchall()
    c.close()
    conn.close()
    return loans


# Reports
def get_top_borrowed(limit=10):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''
        SELECT b.title, b.author, COUNT(l.id) AS borrow_count
        FROM loans l JOIN books b ON l.book_id = b.id
        GROUP BY b.id, b.title, b.author
        ORDER BY borrow_count DESC
        LIMIT %s
    ''', (limit,))
    result = c.fetchall()
    c.close()
    conn.close()
    return result


def get_overdue_report():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''
        SELECT u.full_name, b.title, l.due_date,
               (CURRENT_DATE - l.due_date) AS days_late
        FROM loans l
        JOIN books b ON l.book_id = b.id
        JOIN users u ON l.student_id = u.id
        WHERE l.status IN ('active','overdue') AND l.due_date < CURRENT_DATE
        ORDER BY days_late DESC
    ''')
    result = c.fetchall()
    c.close()
    conn.close()
    return result


def get_fine_summary():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''
        SELECT COALESCE(SUM(amount), 0) AS total_fines,
               COALESCE(SUM(CASE WHEN paid_status='unpaid' THEN amount ELSE 0 END), 0) AS unpaid
        FROM fines
    ''')
    result = c.fetchone()
    c.close()
    conn.close()
    return result


def get_genre_stats():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''
        SELECT genre, COUNT(*) AS count, SUM(copies_total) AS total_copies
        FROM books GROUP BY genre ORDER BY count DESC
    ''')
    result = c.fetchall()
    c.close()
    conn.close()
    return result


def pay_fine(fine_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE fines SET paid_status='paid', paid_date=CURRENT_DATE WHERE id=%s",
        (fine_id,)
    )
    conn.commit()
    c.close()
    conn.close()
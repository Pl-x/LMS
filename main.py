import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import psycopg2

import model

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def librarian_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'librarian':
            flash('Access restricted to librarians.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = model.get_user_by_credentials(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    stats = model.get_dashboard_stats()
    recent_loans = model.get_recent_loans()
    return render_template('dashboard.html', stats=stats, recent_loans=recent_loans)


# Books
@app.route('/books')
@login_required
def books():
    q = request.args.get('q', '')
    genre = request.args.get('genre', '')
    book_list = model.get_all_books(search=q, genre=genre)
    genres = model.get_all_genres()
    return render_template('books.html', books=book_list, genres=genres, q=q, genre=genre)


@app.route('/books/add', methods=['GET', 'POST'])
@login_required
@librarian_required
def add_book():
    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form['author'].strip()
        isbn = request.form.get('isbn', '').strip()
        genre = request.form.get('genre', '').strip()
        copies = int(request.form.get('copies', 1))
        try:
            model.add_book(title, author, isbn, genre, copies)
            flash(f'Book "{title}" added successfully!', 'success')
        except psycopg2.errors.UniqueViolation:
            flash('A book with that ISBN already exists.', 'danger')
        return redirect(url_for('books'))
    return render_template('add_book.html')


@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@librarian_required
def edit_book(book_id):
    book = model.get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books'))
    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form['author'].strip()
        isbn = request.form.get('isbn', '').strip()
        genre = request.form.get('genre', '').strip()
        copies_total = int(request.form.get('copies_total', 1))
        model.update_book(book_id, title, author, isbn, genre, copies_total)
        flash('Book updated successfully!', 'success')
        return redirect(url_for('books'))
    return render_template('edit_book.html', book=book)


@app.route('/books/delete/<int:book_id>', methods=['POST'])
@login_required
@librarian_required
def delete_book(book_id):
    model.delete_book(book_id)
    flash('Book deleted.', 'info')
    return redirect(url_for('books'))


# Members
@app.route('/members')
@login_required
@librarian_required
def members():
    q = request.args.get('q', '')
    member_list = model.get_all_students(search=q)
    return render_template('members.html', members=member_list, q=q)


@app.route('/members/register', methods=['GET', 'POST'])
@login_required
@librarian_required
def register_member():
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        username = request.form['username'].strip()
        password = request.form['password']
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        try:
            model.create_student(username, password, full_name, email, phone)
            flash(f'Student "{full_name}" registered successfully!', 'success')
        except psycopg2.errors.UniqueViolation:
            flash('Username already exists.', 'danger')
        return redirect(url_for('members'))
    return render_template('register_member.html')


@app.route('/loans')
@login_required
@librarian_required
def loans():
    status_filter = request.args.get('status', '')
    model.mark_overdue_loans()
    loan_list = model.get_all_loans(status=status_filter)
    return render_template('loans.html', loans=loan_list, status_filter=status_filter, today=datetime.now().date())


@app.route('/loans/issue', methods=['GET', 'POST'])
@login_required
@librarian_required
def issue_book():
    if request.method == 'POST':
        book_id = int(request.form['book_id'])
        student_id = int(request.form['student_id'])
        due_days = int(request.form.get('due_days', 14))
        book = model.get_book_by_id(book_id)
        if not book or book['copies_available'] < 1:
            flash('Book is not available.', 'danger')
        else:
            issue_date = datetime.now().strftime('%Y-%m-%d')
            due_date = (datetime.now() + timedelta(days=due_days)).strftime('%Y-%m-%d')
            model.create_loan(book_id, student_id, session['user_id'], issue_date, due_date)
            flash(f'Book issued successfully! Due date: {due_date}', 'success')
            return redirect(url_for('loans'))

    books_list = model.get_available_books()
    students = model.get_all_students()
    return render_template('issue_book.html', books=books_list, students=students)


@app.route('/loans/return/<int:loan_id>', methods=['POST'])
@login_required
@librarian_required
def return_book(loan_id):
    loan = model.get_loan_by_id(loan_id)
    if not loan:
        flash('Loan not found.', 'danger')
        return redirect(url_for('loans'))

    return_date = datetime.now().strftime('%Y-%m-%d')
    due = loan['due_date'] 
    today = datetime.now().date()

    fine_amount = None
    if today > due:
        days_late = (today - due).days
        fine_amount = days_late * 10  # KSH 10 per day
        flash(f'Book returned. Fine of KSH {fine_amount} (KSH 10/day × {days_late} days) recorded.', 'warning')
    else:
        flash('Book returned successfully. No fine.', 'success')

    model.return_loan(loan_id, loan['book_id'], return_date, fine_amount)
    return redirect(url_for('loans'))


# Student Views
@app.route('/my-loans')
@login_required
def my_loans():
    if session['role'] != 'student':
        return redirect(url_for('dashboard'))
    loan_list = model.get_my_loans(session['user_id'])
    fines = model.get_my_fines(session['user_id'])
    return render_template('my_loans.html', loans=loan_list, fines=fines)


@app.route('/reports')
@login_required
@librarian_required
def reports():
    return render_template('reports.html',
        top_borrowed=model.get_top_borrowed(),
        overdue_loans=model.get_overdue_report(),
        fine_summary=model.get_fine_summary(),
        genre_stats=model.get_genre_stats()
    )


@app.route('/fines/pay/<int:fine_id>', methods=['POST'])
@login_required
@librarian_required
def pay_fine(fine_id):
    model.pay_fine(fine_id)
    flash('Fine marked as paid.', 'success')
    return redirect(url_for('reports'))


# EntryPoint
if __name__ == '__main__':
    model.init_db()
    app.run(port=5003)
import mysql.connector
from tkinter import *
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import pyotp
import re

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Anurag@123',
    'database': 'BOOKHUB',
    'auth_plugin': 'mysql_native_password'
}

# Establish a database connection
db_conn = mysql.connector.connect(**db_config)
cursor = db_conn.cursor()

# Create tables if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        available BOOLEAN DEFAULT TRUE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_issues (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        book_id INT,
        issue_date DATE,
        return_date DATE,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (book_id) REFERENCES books(id)
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        rent DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
db_conn.commit()


class BookHub:
    def __init__(self, master):
        self.master = master
        master.title("Book Hub")

        self.logged_in = False  # Flag to track login status
        self.logged_in_user_email = None  # Store the email of the logged-in user

        self.label = Label(master, text="Welcome to Book Hub!", font=("Helvetica", 16))
        self.label.pack(pady=20)

        self.login_button = Button(master, text="Login", command=self.login)
        self.login_button.pack(pady=10)

        self.register_button = Button(master, text="Register", command=self.register)
        self.register_button.pack(pady=10)

        # Options visible only to logged-in users
        self.add_book_button = Button(master, text="Add Book", command=self.add_book, state=DISABLED)
        self.add_book_button.pack(pady=10)

        self.show_books_button = Button(master, text="Show Available Books", command=self.show_available_books, state=DISABLED)
        self.show_books_button.pack(pady=10)

        self.issue_book_button = Button(master, text="Issue Book", command=self.issue_book, state=DISABLED)
        self.issue_book_button.pack(pady=10)

        self.request_book_button = Button(master, text="Request Book", command=self.request_book, state=DISABLED)
        self.request_book_button.pack(pady=10)

    def add_book(self):
        add_book_window = Toplevel(self.master)
        add_book_window.title("Add Book")

        title_label = Label(add_book_window, text="Title:")
        title_label.grid(row=0, column=0, padx=10, pady=10)

        title_entry = Entry(add_book_window)
        title_entry.grid(row=0, column=1, padx=10, pady=10)

        author_label = Label(add_book_window, text="Author:")
        author_label.grid(row=1, column=0, padx=10, pady=10)

        author_entry = Entry(add_book_window)
        author_entry.grid(row=1, column=1, padx=10, pady=10)

        add_button = Button(add_book_window, text="Add", command=lambda: self.add_book_to_database(title_entry.get(), author_entry.get(), add_book_window))
        add_button.grid(row=2, column=0, columnspan=2, pady=20)

    def add_book_to_database(self, title, author, add_book_window):
        cursor.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (title, author))
        db_conn.commit()
        messagebox.showinfo("Book Added", "Book added successfully!")
        add_book_window.destroy()

    def show_available_books(self):
        cursor.execute("SELECT * FROM books WHERE available = TRUE")
        books = cursor.fetchall()

        if books:
            available_books_window = Toplevel(self.master)
            available_books_window.title("Available Books")

            book_listbox = Listbox(available_books_window, width=50)
            book_listbox.pack(padx=20, pady=20)

            for book in books:
                book_listbox.insert(END, f"{book[0]}. {book[1]} by {book[2]}")
        else:
            messagebox.showinfo("Available Books", "No available books.")

    def issue_book(self):
        if not self.logged_in:
            messagebox.showinfo("Login Required", "Please log in to issue a book.")
            return

        issue_book_window = Toplevel(self.master)
        issue_book_window.title("Issue Book")

        name_label = Label(issue_book_window, text="Your Name:")
        name_label.grid(row=0, column=0, padx=10, pady=10)

        name_entry = Entry(issue_book_window)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        email_label = Label(issue_book_window, text="Your Email:")
        email_label.grid(row=1, column=0, padx=10, pady=10)

        email_entry = Entry(issue_book_window)
        email_entry.grid(row=1, column=1, padx=10, pady=10)

        book_id_label = Label(issue_book_window, text="Book ID:")
        book_id_label.grid(row=2, column=0, padx=10, pady=10)

        book_id_entry = Entry(issue_book_window)
        book_id_entry.grid(row=2, column=1, padx=10, pady=10)

        issue_button = Button(issue_book_window, text="Issue Book", command=lambda: self.issue_book_to_database(name_entry.get(), email_entry.get(), book_id_entry.get(), issue_book_window))
        issue_button.grid(row=3, column=0, columnspan=2, pady=20)

    def issue_book_to_database(self, name, email, book_id, issue_book_window):
        # Check if the book is available
        cursor.execute("SELECT * FROM books WHERE id = %s AND available = TRUE", (book_id,))
        book = cursor.fetchone()

        if book:
            # Generate and send OTP (for simplicity, let's print it)
            otp = pyotp.TOTP(pyotp.random_base32()).now()
            print(f"OTP for confirmation: {otp}")

            # Get user confirmation
            user_otp = simpledialog.askstring("OTP Confirmation", "Enter OTP to confirm book issue:")

            if user_otp == otp:
                # Issue the book
                issue_date = datetime.now().date()
                return_date = issue_date + timedelta(days=15)
                cursor.execute("""
                    INSERT INTO book_issues (user_id, book_id, issue_date, return_date)
                    VALUES ((SELECT id FROM users WHERE email = %s), %s, %s, %s)
                """, (email, book_id, issue_date, return_date))

                # Mark the book as unavailable
                cursor.execute("UPDATE books SET available = FALSE WHERE id = %s", (book_id,))
                db_conn.commit()

                # Display return warning
                self.display_return_warning(return_date)

                messagebox.showinfo("Book Issued", "Book issued successfully!")
                issue_book_window.destroy()
            else:
                messagebox.showinfo("Invalid OTP", "Invalid OTP. Book issue canceled.")
        else:
            messagebox.showinfo("Book Unavailable", "Book is not available.")

    def display_return_warning(self, return_date):
        current_date = datetime.now().date()
        days_remaining = (return_date - current_date).days

        if days_remaining > 0:
            messagebox.showinfo("Return Warning", f"Please return the book within {days_remaining} days.")
        else:
            late_days = abs(days_remaining)
            penalty = late_days * 50
            messagebox.showinfo("Return Warning", f"Book is {late_days} days overdue. Penalty: Rs. {penalty}")

    def login(self):
        login_window = Toplevel(self.master)
        login_window.title("Login")

        email_label = Label(login_window, text="Email:")
        email_label.grid(row=0, column=0, padx=10, pady=10)

        email_entry = Entry(login_window)
        email_entry.grid(row=0, column=1, padx=10, pady=10)

        password_label = Label(login_window, text="Password:")
        password_label.grid(row=1, column=0, padx=10, pady=10)

        password_entry = Entry(login_window, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)

        login_button = Button(login_window, text="Login", command=lambda: self.verify_login(email_entry.get(), password_entry.get(), login_window))
        login_button.grid(row=2, column=0, columnspan=2, pady=20)

    def verify_login(self, email, password, login_window):
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            self.logged_in = True
            self.logged_in_user_email = email
            self.toggle_visibility()
            messagebox.showinfo("Login Successful", "Login successful!")
            login_window.destroy()
        else:
            messagebox.showerror("Login Failed", "Invalid email or password.")

    def register(self):
        register_window = Toplevel(self.master)
        register_window.title("Register")

        email_label = Label(register_window, text="Email:")
        email_label.grid(row=0, column=0, padx=10, pady=10)

        email_entry = Entry(register_window)
        email_entry.grid(row=0, column=1, padx=10, pady=10)

        password_label = Label(register_window, text="Password:")
        password_label.grid(row=1, column=0, padx=10, pady=10)

        password_entry = Entry(register_window, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)

        register_button = Button(register_window, text="Register", command=lambda: self.register_user(email_entry.get(), password_entry.get(), register_window))
        register_button.grid(row=2, column=0, columnspan=2, pady=20)

    def register_user(self, email, password, register_window):
        # Use regular expression to validate email format
        email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@(email\.com|outlook\.com|otherrealdomain\.com)$')
        if email_pattern.match(email):
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            db_conn.commit()
            messagebox.showinfo("Registration Successful", "User registered successfully!")
            register_window.destroy()
        else:
            messagebox.showerror("Invalid Email", "Please use a valid email address with domain email.com, outlook.com, or otherrealdomain.com")

    def request_book(self):
        if not self.logged_in:
            messagebox.showinfo("Login Required", "Please log in to request a book.")
            return

        request_book_window = Toplevel(self.master)
        request_book_window.title("Request Book")

        title_label = Label(request_book_window, text="Title:")
        title_label.grid(row=0, column=0, padx=10, pady=10)

        title_entry = Entry(request_book_window)
        title_entry.grid(row=0, column=1, padx=10, pady=10)

        author_label = Label(request_book_window, text="Author:")
        author_label.grid(row=1, column=0, padx=10, pady=10)

        author_entry = Entry(request_book_window)
        author_entry.grid(row=1, column=1, padx=10, pady=10)

        request_button = Button(request_book_window, text="Request", command=lambda: self.request_book_to_database(title_entry.get(), author_entry.get(), request_book_window))
        request_button.grid(row=2, column=0, columnspan=2, pady=20)

    def request_book_to_database(self, title, author, request_book_window):
        # Check if the book is already requested by the user
        cursor.execute("SELECT * FROM book_requests WHERE user_id = (SELECT id FROM users WHERE email = %s) AND title = %s AND author = %s", (self.logged_in_user_email, title, author))
        existing_request = cursor.fetchone()

        if existing_request:
            messagebox.showinfo("Already Requested", "You have already requested this book.")
        else:
            # Insert the book request into the database
            cursor.execute("""
                INSERT INTO book_requests (user_id, title, author)
                VALUES ((SELECT id FROM users WHERE email = %s), %s, %s)
            """, (self.logged_in_user_email, title, author))
            db_conn.commit()
            messagebox.showinfo("Book Requested", "Book requested successfully!")
            request_book_window.destroy()

    def toggle_visibility(self):
        # Enable or disable options based on login status
        if self.logged_in:
            self.add_book_button['state'] = NORMAL
            self.show_books_button['state'] = NORMAL
            self.issue_book_button['state'] = NORMAL
            self.request_book_button['state'] = NORMAL
        else:
            self.add_book_button['state'] = DISABLED
            self.show_books_button['state'] = DISABLED
            self.issue_book_button['state'] = DISABLED
            self.request_book_button['state'] = DISABLED

    def add_own_book(self):
        if not self.logged_in:
            messagebox.showinfo("Login Required", "Please log in to add your book.")
            return

        add_own_book_window = Toplevel(self.master)
        add_own_book_window.title("Add Your Book with Rent")

        title_label = Label(add_own_book_window, text="Title:")
        title_label.grid(row=0, column=0, padx=10, pady=10)

        title_entry = Entry(add_own_book_window)
        title_entry.grid(row=0, column=1, padx=10, pady=10)

        author_label = Label(add_own_book_window, text="Author:")
        author_label.grid(row=1, column=0, padx=10, pady=10)

        author_entry = Entry(add_own_book_window)
        author_entry.grid(row=1, column=1, padx=10, pady=10)

        rent_label = Label(add_own_book_window, text="Rent (Rs.):")
        rent_label.grid(row=2, column=0, padx=10, pady=10)

        rent_entry = Entry(add_own_book_window)
        rent_entry.grid(row=2, column=1, padx=10, pady=10)

        add_button = Button(add_own_book_window, text="Add",
                            command=lambda: self.add_own_book_to_database(title_entry.get(), author_entry.get(),
                                                                          rent_entry.get(), add_own_book_window))
        add_button.grid(row=3, column=0, columnspan=2, pady=20)

    def add_own_book_to_database(self, title, author, rent, add_own_book_window):
        cursor.execute("""
            INSERT INTO user_books (user_id, title, author, rent)
            VALUES ((SELECT id FROM users WHERE email = %s), %s, %s, %s)
        """, (self.logged_in_user_email, title, author, rent))
        db_conn.commit()
        messagebox.showinfo("Book Added", "Your book added successfully!")
        add_own_book_window.destroy()


# Create the GUI window
root = Tk()
app = BookHub(root)

# Run the GUI
root.mainloop()

# Close the database connection
cursor.close()
db_conn.close()

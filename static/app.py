import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from functools import wraps
from datetime import datetime

# Get the absolute path of the directory containing this file
basedir = os.path.abspath(os.path.dirname(__file__))

# Create the Flask app instance
app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'))
app.secret_key = "Reddy@2001"  # Needed for flash messages and session

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Reddy@2001',
    'database': 'test'
}

# Database connection function
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT id, email, password FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                
                if user:
                    user_id, user_email, hashed_password = user
                    if check_password_hash(hashed_password, password):
                        session['user_id'] = user_id
                        print(session['user_id'])
                        return redirect(url_for('home'))
                    else:
                        flash("Invalid email or password", "error")
                else:
                    flash("User not found", "error")
                
                return redirect(url_for('login'))
            except mysql.connector.Error as e:
                print(f"Error: {e}")
                flash("An error occurred during login. Please try again.", "error")
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Unable to connect to the database. Please try again later.", "error")
    
    return render_template('login.html')

@app.route("/home")
def home():
    if 'user_id' in session:
        print(session['user_id'])
        return render_template("index.html")
    else:
        # If user is not logged in, redirect to login page

        return redirect(url_for('login'))


@app.route("/about")
def about():



    return render_template("about.html")


@app.route("/services")
def services():
    return render_template("services.html")




@app.route("/pricing")
def pricing():
    return render_template("pricing.html")      
    

@app.route("/contact")
def contact():


    return render_template("contact.html")  

@app.route("/events")
def events():
    return render_template("events.html")  

@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")   

@app.route("/bookings")
def bookings():
    return render_template("bookings.html")


@app.route("/register") 
def register():
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])


def signup():
    if request.method == 'POST':
        # Retrieve form data for user signup
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')

        # Check if all required fields are present
        if not all([full_name, email, password, confirm_password, phone]):
            flash('All fields are required.', 'error')
            return render_template('signup.html')

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('signup.html')

        # Hash the password

        hashed_password = generate_password_hash(password)

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # SQL query to insert data into the users table
                sql = """INSERT INTO users 
                         (full_name, email, password, phone) 
                         VALUES (%s, %s, %s, %s)"""
                values = (full_name, email, hashed_password, phone)

                # Execute the query
                cursor.execute(sql, values)
            connection.commit()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Error as e:
            if 'Duplicate entry' in str(e):
                flash('An account with this email already exists.', 'error')
            else:



                flash('An error occurred. Please try again.', 'error')
        except Exception as e:
            print(f"Unexpected error: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
        finally:
            if connection:
                connection.close()

    return render_template('signup.html')

@app.route("/book", methods=['GET', 'POST'])
def book_event():
    if request.method == 'POST':
        # Retrieve form data for event booking
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        event_type = request.form.get('event_type')
        event_date = request.form.get('event_date')
        guests = request.form.get('guests')
        special_requests = request.form.get('special_requests')

        # Check if all required fields are present
        if not all([full_name, email, phone, event_type, event_date, guests]):
            flash('All fields except special requests are required.', 'error')
            return render_template('book_event.html')

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # SQL query to insert data into the event_bookings table
                sql = """INSERT INTO event_bookings 
                         (full_name, email, phone, event_type, event_date, guests, special_requests) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                values = (full_name, email, phone, event_type, event_date, guests, special_requests)

                # Execute the query
                cursor.execute(sql, values)

            connection.commit()

            flash('Event booked successfully! Thank you!', 'success')
            return render_template('booking_success.html')
        except Exception as e:
            print(f"Unexpected error: {e}")
            flash("An error occurred while booking the event. Please try again.", 'error')
        finally:
            if connection:
                connection.close()

    return render_template('book_event.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    if conn is None:
        flash("Unable to connect to the database", "error")
        return redirect(url_for('index'))

    cursor = conn.cursor(dictionary=True)

    # Fetch all event bookings
    cursor.execute('''
        SELECT id, full_name, email, event_type, event_date, guests, special_requests
        FROM event_bookings
        ORDER BY event_date DESC
    ''')
    
    events = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('dashboard.html', events=events)

@app.route('/history')
def history():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to view the history.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash("Unable to connect to the database", "error")
        return redirect(url_for('index'))

    cursor = conn.cursor()  # Remove the dictionary=True argument

    # Fetch all event bookings
    cursor.execute('''
        SELECT id, full_name, email, phone, event_type, event_date, guests, special_requests
        FROM event_bookings
        ORDER BY event_date DESC
    ''')
    
    # Fetch column names
    columns = [column[0] for column in cursor.description]
    
    # Fetch all rows and convert to list of dictionaries
    events = []
    for row in cursor.fetchall():
        events.append(dict(zip(columns, row)))
    
    cursor.close()
    conn.close()

    return render_template('history.html', events=events)

@app.context_processor
def utility_processor():
    def now():
        return datetime.now()
    return dict(now=now)

if __name__ == "__main__":



    print(f"Template folder: {app.template_folder}")  # Debug print
    app.run(debug=True)
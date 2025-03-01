from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Secret key for session management
app.secret_key = "supersecretkey"

# Database configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)


# Workout model
class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    exercise = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes

# Create database tables within app context
with app.app_context():
    db.create_all()

# Home Route (Register & Login Page)
@app.route('/')
def home():
    return render_template('register_login.html')

# Register Route
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not username or not email or not password:
        flash("All fields are required!", "danger")
        return redirect(url_for('home'))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email already registered! Please log in.", "warning")
        return redirect(url_for('home'))

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, email=email, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    flash("Registration successful! Please log in.", "success")
    return redirect(url_for('home'))

# Login Route
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['username'] = user.username
        flash(f"Welcome, {user.username}!", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid email or password. Try again.", "danger")
        return redirect(url_for('home'))

# Dashboard Route (Protected)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('home'))

    return render_template('dashboard.html', username=session['username'])

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))


# Track Workouts Route
@app.route('/track_workouts', methods=['GET', 'POST'])
def track_workouts():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        date_str = request.form.get('date')
        exercise = request.form.get('exercise')
        duration = request.form.get('duration')

        if not date_str or not exercise or not duration:
            flash("All fields are required!", "danger")
            return redirect(url_for('track_workouts'))

        # Convert date string to Python date object
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        new_workout = Workout(user_id=session['user_id'], date=date_obj, exercise=exercise, duration=int(duration))
        db.session.add(new_workout)
        db.session.commit()

        flash("Workout added successfully!", "success")
        return redirect(url_for('view_workouts'))

    return render_template('track_workouts.html')


# View Workouts Route
@app.route('/workouts')
def view_workouts():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('home'))
    


    workouts = Workout.query.filter_by(user_id=session['user_id']).all()
    return render_template('view_workouts.html', workouts=workouts)

# Add Workout Route
@app.route('/add_workout', methods=['GET', 'POST'])
def add_workout():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        date = request.form.get('date')
        exercise = request.form.get('exercise')
        duration = request.form.get('duration')

        if not date or not exercise or not duration:
            flash("All fields are required!", "danger")
            return redirect(url_for('add_workout'))


        new_workout = Workout(user_id=session['user_id'], date=date, exercise=exercise, duration=duration)
        db.session.add(new_workout)
        db.session.commit()

        flash("Workout added successfully!", "success")
        return redirect(url_for('view_workouts'))

    return render_template('add_workout.html')

# Edit Workout Route
@app.route('/edit_workout/<int:id>', methods=['GET', 'POST'])
def edit_workout(id):
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('home'))

    workout = Workout.query.get_or_404(id)

    if request.method == 'POST':
        workout.date = request.form.get('date')
        workout.exercise = request.form.get('exercise')
        workout.duration = request.form.get('duration')

        db.session.commit()
        flash("Workout updated successfully!", "success")
        return redirect(url_for('view_workouts'))

    return render_template('edit_workout.html', workout=workout)

# Delete Workout Route
@app.route('/delete_workout/<int:id>', methods=['POST'])
def delete_workout(id):
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('home'))

    workout = Workout.query.get_or_404(id)
    db.session.delete(workout)
    db.session.commit()

    flash("Workout deleted successfully!", "success")
    return redirect(url_for('view_workouts'))



""" 
# View Progress Route
@app.route('/view_progress')
def view_progress():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('home'))

    try:
        # Fetch all workouts for the logged-in user
        workouts = Workout.query.filter_by(user_id=session['user_id']).all()
        print(workouts)

        # Calculate progress (e.g., total duration of workouts, number of workouts, etc.)
        total_duration = sum(workout.duration for workout in workouts)
        total_workouts = len(workouts)
    except:
        total_duration = 0
        total_workouts = 0
    # Pass the progress data to the template
    return render_template('view_progress.html', total_duration=total_duration, total_workouts=total_workouts)

""" 
# View Progress Route
@app.route('/view_progress')
def view_progress():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('home'))

    try:
        # Fetch all workouts for the logged-in user
        workouts = Workout.query.filter_by(user_id=session['user_id']).all()

        # Calculate progress (e.g., total duration of workouts, number of workouts, etc.)
        total_duration = sum(workout.duration for workout in workouts)
        total_workouts = len(workouts)
    except:
        workouts = []
        total_duration = 0
        total_workouts = 0

    # Pass the progress data and workouts to the template
    return render_template('view_progress.html', total_duration=total_duration, total_workouts=total_workouts, workouts=workouts)

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)

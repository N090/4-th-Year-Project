from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

roles = ["solo-client", "client", "trainer"]
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Add a secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@127.0.0.1/swiftlift'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    # Define relationship with WorkoutProgram
    workout_programs = db.relationship('WorkoutProgram', backref='user', lazy=True)

# Define Exercises model
class Exercises(db.Model):
    __tablename__ = 'Exercises'
    e_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    muscle_group = db.Column(db.ARRAY(db.String(50)), nullable=False)
    equipment = db.Column(db.String(100), nullable=False)

# Define WorkoutProgram model
class WorkoutProgram(db.Model):
    __tablename__ = 'workout_program'
    workout_id = db.Column(db.Integer, primary_key=True)
    w_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    difficulty = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)

class WorkoutProgramExercises(db.Model):
    __tablename__ = 'workout_exercises'
    workout_id = db.Column(db.Integer, db.ForeignKey('workout_programs.workout_id'), primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.e_id'), primary_key=True)

# Home page
@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', message='Username already exists. Please choose a different one.')

        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html', roles=roles)

# Login route
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username  # Store username in session
            return redirect(url_for('main'))
        else:
            return render_template('login.html', message='Invalid username or password')

    return render_template('login.html')

# Main route
@app.route('/main')
def main():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('main.html', username=username, role=user.role)
    return redirect(url_for('login'))

# Update the Flask route for workout_program to pass the exercises variable
@app.route('/workout_program')
def workout_program():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            if user.role == "solo-client" or user.role == "client":
                # Get the workout program for the user
                workout = WorkoutProgram.query.filter_by(user_id=user.id).first()
                # Query all exercises
                exercises = Exercises.query.all()
                return render_template('workout_program.html', role=user.role, workout=workout, exercises=exercises)
            elif user.role == "trainer":
                # Get all workout programs for the trainer
                workouts = WorkoutProgram.query.all()
                # Query all exercises
                exercises = Exercises.query.all()
                return render_template('workout_program.html', role=user.role, workouts=workouts, exercises=exercises)
    return redirect(url_for('login'))

# Update the Flask route to use the Exercise model
@app.route('/create_workout', methods=['POST'])
def create_workout():
    if request.method == 'POST':
        username = session.get('username')
        if username:
            user = User.query.filter_by(username=username).first()
            if user and user.role == "trainer":
                w_name = request.form['name']
                description = request.form['description']
                difficulty = request.form['difficulty']
                
                # Create a new workout program
                new_workout = WorkoutProgram(w_name=w_name, description=description, difficulty=difficulty, user_id=user.id)
                db.session.add(new_workout)
                db.session.commit()
                
                # Query exercises from the database
                exercises = Exercises.query.all()
                
                return render_template('workout_program.html', role=user.role, exercises=exercises)
                
    return redirect(url_for('workout_program'))

@app.route('/delete_workout/<int:id>')
def delete_workout(id):
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and user.role == "trainer":
            # Delete associated exercises
            WorkoutProgramExercises.query.filter_by(workout_id=id).delete()
            
            # Delete the workout program
            workout = WorkoutProgram.query.get(id)
            db.session.delete(workout)
            db.session.commit()
    return redirect(url_for('workout_program'))

# Nutrition Program route
@app.route('/nutrition_program')
def nutrition_program():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('nutrition_program.html', role=user.role)
    return redirect(url_for('login'))

# Client route
@app.route('/client')
def client():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('client.html', role=user.role)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

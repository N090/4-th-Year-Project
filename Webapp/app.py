from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

roles = ["solo-client", "client", "trainer"]

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@127.0.0.1/swiftlift'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    __tablename__ = 'Users'  # Update table name to 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    # Define relationship with WorkoutProgram
    workout_programs = db.relationship('WorkoutProgram', backref='user', lazy=True)
    nutrition_programs = db.relationship('NutritionProgram', backref='user', lazy=True)


# Define Exercises model
class Exercises(db.Model):
    __tablename__ = 'exercises'
    e_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    muscle_group = db.Column(db.ARRAY(db.String(50)), nullable=False)
    equipment = db.Column(db.String(100), nullable=False)

class WorkoutProgram(db.Model):
    __tablename__ = 'workout_program'

    workout_id = db.Column(db.Integer, primary_key=True)
    w_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    difficulty = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # Fix foreign key reference

    owner = db.relationship('User', backref=db.backref('owned_workout_programs', lazy=True))
    exercises = db.relationship('Exercises', secondary='workout_exercises')

class WorkoutProgramExercises(db.Model):
    __tablename__ = 'workout_exercises'
    workout_id = db.Column(db.Integer, db.ForeignKey('workout_program.workout_id'), primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.e_id'), primary_key=True)
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)

    exercise = db.relationship('Exercises')

class Food(db.Model):
    __tablename__ = 'food'
    food_id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(50), nullable=False)
    calories_serving = db.Column(db.Numeric, nullable=False)
    serving_size = db.Column(db.String(20), nullable=False)
    carbs = db.Column(db.Integer, nullable=False)
    fat = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Integer, nullable=False)

class Meal(db.Model):
    __tablename__ = 'meal'
    meal_id = db.Column(db.Integer, primary_key=True)
    meal_name = db.Column(db.String(50))
    nutrition_programs = db.relationship('NutritionProgram', backref='meal', lazy=True)

class NutritionProgram(db.Model):
    __tablename__ = 'nutrition_program'
    n_id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.meal_id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.food_id'), nullable=False)
    serving_size = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)


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
            session['username'] = username
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


@app.route('/add_exercises_to_workout/<int:workout_id>', methods=['GET', 'POST'])
def add_exercises_to_workout(workout_id):
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and (user.role == "solo-client" or user.role == "trainer"):
            if request.method == 'POST':
                # Handle form submission to add exercises to the workout
                exercise_id = request.form['exercise_id']
                sets = request.form['sets']
                reps = request.form['reps']

                # Check if the workout_id exists
                existing_workout = WorkoutProgram.query.get(workout_id)
                if existing_workout:
                    # Add the exercise to the workout
                    workout_exercise = WorkoutProgramExercises(workout_id=workout_id, exercise_id=exercise_id, sets=sets, reps=reps)
                    db.session.add(workout_exercise)
                    db.session.commit()

            # Fetch current exercises added to the workout
            current_workout_exercises = WorkoutProgramExercises.query.filter_by(workout_id=workout_id).all()

            # Render the page to continue adding exercises with current workout exercises displayed
            exercises = Exercises.query.all()
            return render_template('add_exercises.html', exercises=exercises, workout_id=workout_id, current_workout_exercises=current_workout_exercises)

    # Render the page to add exercises
    exercises = Exercises.query.all()
    return render_template('add_exercises.html', exercises=exercises, workout_id=workout_id)

@app.route('/remove_exercise/<int:workout_id>/<int:exercise_id>', methods=['POST'])
def remove_exercise(workout_id, exercise_id):
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and (user.role == "solo-client" or user.role == "trainer"):
            exercise_id = request.form['exercise_id']

            # Add logic to remove the exercise from the workout
            workout_exercise = WorkoutProgramExercises.query.filter_by(workout_id=workout_id, exercise_id=exercise_id).first()
            if workout_exercise:
                db.session.delete(workout_exercise)
                db.session.commit()

    # After removing the exercise, fetch the updated list of exercises for the current workout
    current_workout_exercises = WorkoutProgramExercises.query.filter_by(workout_id=workout_id).all()

    # Render the page to add exercises with the updated list of exercises
    exercises = Exercises.query.all()
    return render_template('add_exercises.html', exercises=exercises, workout_id=workout_id, current_workout_exercises=current_workout_exercises)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            if request.method == 'POST':
                old_password = request.form.get('old_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if not old_password or not new_password or not confirm_password:
                    error_message = 'All fields are required.'
                    return render_template('change_password.html', error_message=error_message)

                if user.password != old_password:
                    error_message = 'Incorrect old password. Please try again.'
                    return render_template('change_password.html', error_message=error_message)
                
                if new_password != confirm_password:
                    error_message = 'New passwords do not match. Please try again.'
                    return render_template('change_password.html', error_message=error_message)
                
                # Update the user's password in the database
                user.password = new_password
                db.session.commit()
                
                success_message = 'Password has been changed successfully!'
                return render_template('change_password.html', success_message=success_message)
            else:
                return render_template('change_password.html')
    return redirect(url_for('login'))

@app.route('/delete_workout_solo/<int:id>')
def delete_workout_solo(id):
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and (user.role == "solo-client" or user.role == "client"):
            WorkoutProgramExercises.query.filter_by(workout_id=id).delete()
            workout = WorkoutProgram.query.get(id)
            db.session.delete(workout)
            db.session.commit()
    return redirect(url_for('workout_program'))

@app.route('/workout_program')
def workout_program():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            workouts = WorkoutProgram.query.all()
            exercises = Exercises.query.all()
            return render_template('workout_program.html', role=user.role, workouts=workouts, exercises=exercises)
    return redirect(url_for('login'))

# Function to initialize the current workout program in the session
def initialize_current_workout():
    session['current_workout'] = {
        'name': None,
        'description': None,
        'difficulty': None,
        'exercises': []  # List to store added exercises
    }

# Function to add an exercise to the current workout program
def add_exercise_to_current_workout(exercise_id, sets, reps):
    if 'current_workout' not in session:
        initialize_current_workout()
    session['current_workout']['exercises'].append({
        'exercise_id': exercise_id,
        'sets': sets,
        'reps': reps
    })


@app.route('/create_workout', methods=['GET', 'POST'])
def create_workout():
    if request.method == 'POST':
        username = session.get('username')
        if username:
            user = User.query.filter_by(username=username).first()
            if user and user.role == "trainer":
                # Collect workout details
                w_name = request.form['name']
                description = request.form['description']
                difficulty = request.form['difficulty']

                # Create workout program in the session
                initialize_current_workout()
                session['current_workout']['name'] = w_name
                session['current_workout']['description'] = description
                session['current_workout']['difficulty'] = difficulty

                # Redirect to the page to add exercises, passing workout_id parameter
                new_workout = WorkoutProgram(w_name=w_name, description=description, difficulty=difficulty, user_id=user.id)
                db.session.add(new_workout)
                db.session.commit()

                # Redirect to the page to add exercises, passing workout_id parameter
                return redirect(url_for('add_exercises_to_workout', workout_id=new_workout.workout_id))

    return redirect(url_for('workout_program'))


# Route for finalizing the workout creation
@app.route('/finalize_workout', methods=['POST'])
def finalize_workout():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and user.role == "trainer":
            if request.method == 'POST':
                # Retrieve the current workout program from the session
                current_workout = session.get('current_workout')
                if current_workout:
                    # Create workout program in the database
                    new_workout = WorkoutProgram(
                        w_name=current_workout['name'],
                        description=current_workout['description'],
                        difficulty=current_workout['difficulty'],
                        user_id=user.id
                    )
                    db.session.add(new_workout)
                    db.session.commit()

                    # Retrieve the ID of the newly created workout
                    workout_id = new_workout.workout_id

                    # Add exercises to the workout program
                    for exercise in current_workout['exercises']:
                        workout_exercises = WorkoutProgramExercises(
                            workout_id=workout_id,
                            exercise_id=exercise['exercise_id'],
                            sets=exercise['sets'],
                            reps=exercise['reps']
                        )
                        db.session.add(workout_exercises)

                    db.session.commit()

                    # Clear the current workout from session
                    session.pop('current_workout')

                    # Redirect to the workout program page
                    return redirect(url_for('workout_program'))

    return redirect(url_for('workout_program'))

@app.route('/delete_workout/<int:id>', methods=['POST'])
def delete_workout(id):
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and user.role == "trainer":
            # Check if the workout with the given ID exists
            workout = WorkoutProgram.query.get(id)
            if workout:
                # Delete associated workout exercises
                WorkoutProgramExercises.query.filter_by(workout_id=id).delete()
                # Delete the workout
                db.session.delete(workout)
                db.session.commit()
    return redirect(url_for('workout_program'))


@app.route('/nutrition_program')
def nutrition_program():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('nutrition_program.html', role=user.role)
    return redirect(url_for('login'))

@app.route('/exercise_details/<int:exercise_id>')
def exercise_details(exercise_id):
    exercise = Exercises.query.get(exercise_id)
    if exercise:
        return jsonify({
            'name': exercise.name,
            'description': exercise.description,
            'muscle_group': exercise.muscle_group,
            'equipment': exercise.equipment,
        })
    else:
        return jsonify({'error': 'Exercise not found'}), 404


@app.route('/client')
def client():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('client.html', role=user.role)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('homepage'))

if __name__ == '__main__':
    app.run(debug=True)

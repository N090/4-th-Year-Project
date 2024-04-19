from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import requests

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

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), unique=True)
    user = db.relationship('User', backref='client', uselist=False)

class Trainer(db.Model):
    __tablename__ = 'trainers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    user = db.relationship('User', backref='trainer')

class ClientTrainerAssignment(db.Model):
    __tablename__ = 'client_trainer_assignment'

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), primary_key=True)


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

# Define Food model
class Food(db.Model):
    __tablename__ = 'food'
    food_id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(50), nullable=False)
    calories_serving = db.Column(db.Numeric, nullable=False)
    serving_size = db.Column(db.String(20), nullable=False)
    carbs = db.Column(db.Integer, nullable=False)
    fat = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Integer, nullable=False)

    # Relationship with FoodNutritionProgram
    food_nutrition_programs_relationship = db.relationship('FoodNutritionProgram', backref='food_entry', lazy=True)

# Define NutritionProgram model
class NutritionProgram(db.Model):
    __tablename__ = 'nutrition_program'
    n_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # Fix the foreign key reference
    n_name = db.Column(db.String(50))
    n_description = db.Column(db.Text)
    n_difficulty = db.Column(db.String(20)) 

    # Define relationship with User
    owner = db.relationship("User", backref='owned_nutrition_programs')
    # Relationship with FoodNutritionProgram
    food_nutrition_programs = db.relationship('FoodNutritionProgram', backref='nutrition_program_entry')

class FoodNutritionProgram(db.Model):
    __tablename__ = 'food_nutrition_program'
    food_nutrition_program_id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('food.food_id'), nullable=False)
    nutrition_program_id = db.Column(db.Integer, db.ForeignKey('nutrition_program.n_id'), nullable=False)

    # Define relationships
    food = db.relationship('Food', backref='food_nutrition_program_entries')
    nutrition_program = db.relationship('NutritionProgram', backref='food_entry_nutrition_programs')

# Define a model to represent the assignment of workout programs to clients
class AssignedWorkoutProgram(db.Model):
    __tablename__ = 'assigned_workout_program'

    id = db.Column(db.Integer, primary_key=True)
    workout_program_id = db.Column(db.Integer, db.ForeignKey('workout_program.workout_id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), nullable=False)

    # Define relationships
    workout_program = db.relationship('WorkoutProgram', backref='assigned_clients')
    client = db.relationship('Client', backref='assigned_workout_programs')
    trainer = db.relationship('Trainer')

# Define a model to represent the assignment of nutrition programs to clients
class AssignedNutritionProgram(db.Model):
    __tablename__ = 'assigned_nutrition_program'

    id = db.Column(db.Integer, primary_key=True)
    nutrition_program_id = db.Column(db.Integer, db.ForeignKey('nutrition_program.n_id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), nullable=False)

    # Define relationships
    nutrition_program = db.relationship('NutritionProgram', backref='assigned_clients')
    client = db.relationship('Client', backref='assigned_nutrition_programs')
    trainer = db.relationship('Trainer')


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

        # Check the role selected and create the appropriate user instance
        if role == "client":
            new_client = Client(user_id=new_user.id)
            db.session.add(new_client)
            db.session.commit()
        elif role == "trainer":
            new_trainer = Trainer(user_id=new_user.id)
            db.session.add(new_trainer)
            db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html', roles=roles)



@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username

            # Check user role
            if user.role == 'trainer':
                # Get the trainer associated with the user
                trainer = Trainer.query.filter_by(user_id=user.id).first()
                if trainer:
                    session['trainer_id'] = trainer.id  # Store trainer ID in session

            elif user.role == 'client':
                # Get the client associated with the user
                client = Client.query.filter_by(user_id=user.id).first()
                if client:
                    session['client_id'] = client.id  # Store client ID in session

            # Redirect to appropriate page based on role
            return redirect(url_for('main'))

        # If the user doesn't exist or invalid credentials, render login page with a message
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

@app.route('/bmi', methods=['GET', 'POST'])
def calculate_bmi():
    if request.method == 'POST':
        # Handle the form submission for BMI calculation
        # You can access form data using request.form
        # Perform BMI calculation logic here
        pass  # Placeholder for BMI calculation logic
    return render_template('bmi.html')

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

@app.route('/nutrition_program', methods=['GET', 'POST'])
def nutrition_program():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            if request.method == 'POST':
                # Process POST request if needed
                pass
                
            # Retrieve nutrition programs for the logged-in user
            if user.role == "trainer":
                nutrition_programs = NutritionProgram.query.filter_by(user_id=user.id).all()
            else:
                nutrition_programs = NutritionProgram.query.all()
                
            # Render the HTML template with the retrieved nutrition programs
            return render_template('nutrition_program.html', role=user.role, nutrition_programs=nutrition_programs)
    
    # Redirect to the main page if user is not logged in or doesn't have appropriate role
    return redirect(url_for('main'))


# Function to initialize the current nutrition program in the session
def initialize_current_nutrition():
    session['current_nutrition'] = {
        'name': None,
        'description': None,
        'difficulty': None,
        'food': []  # List to store added meals
    }

@app.route('/delete_nutrition_program/<int:id>', methods=['POST'])
def delete_nutrition_program(id):
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and user.role == "trainer":
            # Check if the nutrition program with the given ID exists
            nutrition_program = NutritionProgram.query.get(id)
            if nutrition_program:
                # Delete associated nutrition program foods
                FoodNutritionProgram.query.filter_by(nutrition_program_id=id).delete()
                # Delete the nutrition program
                db.session.delete(nutrition_program)
                db.session.commit()
    return redirect(url_for('nutrition_program'))


@app.route('/add_food')
def add_food():
    # Check if the user is logged in
    username = session.get('username')
    # Fetch user and validate role
    user = User.query.filter_by(username=username).first()
    if not user or user.role != "trainer":
        return redirect(url_for('login'))  # Redirect if user is not a trainer
    # Handle POST request to add food to meal
    if request.method == 'POST':
        # Redirect to the nutrition program page
        return redirect(url_for('nutrition_program'))
    # Handle GET request to render the form to add foods
    else:
        # Fetch foods data
        foods = Food.query.all()
        # Pass the user object and a default value for nutrition_id to the template
        return render_template('add_food.html', foods=foods, user=user, nutrition_id=None)


# Function to add food to the current nutrition program
def add_food_to_current_nutrition_program(food_id):
    if 'current_nutrition' not in session:
        initialize_current_nutrition()
    session['current_nutrition']['meals'].append({
        'food_id': food_id,
    })

@app.route('/create_nutrition_program', methods=['GET', 'POST'])
def create_nutrition_program():
    if request.method == 'POST':
        username = session.get('username')
        if username:
            user = User.query.filter_by(username=username).first()
            if user and user.role == "trainer":
                # Collect nutrition program details
                n_name = request.form['n_name']
                n_description = request.form['n_description']
                n_difficulty = request.form['n_difficulty']

                # Create nutrition program in the session
                initialize_current_nutrition()
                session['current_nutrition']['name'] = n_name
                session['current_nutrition']['description'] = n_description
                session['current_nutrition']['difficulty'] = n_difficulty

                # Create the NutritionProgram instance and add it to the database
                new_nutrition_program = NutritionProgram(
                    n_name=n_name,
                    n_description=n_description,
                    n_difficulty=n_difficulty,
                    user_id=user.id
                )
                db.session.add(new_nutrition_program)
                db.session.commit()

                # Redirect to the page to add foods, passing nutrition_program_id parameter
                return redirect(url_for('add_food_to_nutrition', nutrition_id=new_nutrition_program.n_id))

    return redirect(url_for('nutrition_program'))

@app.route('/add_food_to_nutrition/<int:nutrition_id>', methods=['GET', 'POST'])
def add_food_to_nutrition(nutrition_id):
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and (user.role == "solo-client" or user.role == "trainer"):
            if request.method == 'POST':
                # Handle form submission to add food to the nutrition program
                food_id = request.form['food_id']

                # Check if the nutrition_id exists
                existing_nutrition = NutritionProgram.query.get(nutrition_id)
                if existing_nutrition:
                    # Add the food to the nutrition program
                    food_nutrition_program = FoodNutritionProgram(food_id=food_id, nutrition_program_id=nutrition_id)
                    db.session.add(food_nutrition_program)
                    db.session.commit()

            # Fetch current foods added to the nutrition program
            current_nutrition_foods = FoodNutritionProgram.query.filter_by(nutrition_program_id=nutrition_id).all()

            # Render the page to continue adding foods with current nutrition foods displayed
            foods = Food.query.all()
            return render_template('add_food.html', foods=foods, nutrition_id=nutrition_id, current_nutrition_foods=current_nutrition_foods)

    # Render the page to add foods
    foods = Food.query.all()
    current_nutrition_foods = []  # Ensure an empty list is passed if the user is not authenticated or authorized
    return render_template('add_food.html', foods=foods, nutrition_id=nutrition_id, current_nutrition_foods=current_nutrition_foods)

@app.route('/remove_food/<int:nutrition_id>/<int:food_id>', methods=['POST'])
def remove_food(nutrition_id, food_id):
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and (user.role == "solo-client" or user.role == "trainer"):
            if request.method == 'POST':
                # Get the food_id from the form data
                food_id = request.form['food_id']

                # Remove the food from the nutrition program
                food_nutrition_program = FoodNutritionProgram.query.filter_by(nutrition_program_id=nutrition_id, food_id=food_id).first()
                if food_nutrition_program:
                    db.session.delete(food_nutrition_program)
                    db.session.commit()

    # After removing the food, fetch the updated list of foods for the current nutrition program
    current_nutrition_foods = FoodNutritionProgram.query.filter_by(nutrition_program_id=nutrition_id).all()

    # Render the page to add foods with the updated list of foods
    foods = Food.query.all()
    return render_template('add_food.html', foods=foods, nutrition_id=nutrition_id, current_nutrition_foods=current_nutrition_foods)

@app.route('/fetch_food')
def fetch_food():
    foods = Food.query.all()
    food_data = [{'food_id': food.food_id, 'food_name': food.food_name} for food in foods]
    return jsonify(food_data)

@app.route('/fetch_food_details/<int:food_id>')
def fetch_food_details(food_id):
    food = Food.query.get(food_id)
    if food:
        food_details = {
            'food_name': food.food_name,
            'calories_serving': food.calories_serving,
            'serving_size': food.serving_size,
            'carbs': food.carbs,
            'fat': food.fat,
            'protein': food.protein
        }
        return jsonify(food_details)
    else:
        return jsonify({'error': 'Food not found'}), 404


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
            if user.role == 'trainer':
                trainer_id = session.get('trainer_id')  # Retrieve trainer ID from session
                if not trainer_id:
                    # If trainer ID is not in session, retrieve it from the database
                    trainer = Trainer.query.filter_by(user_id=user.id).first()
                    if trainer:
                        trainer_id = trainer.id
                        session['trainer_id'] = trainer_id  # Store trainer ID in session
                    else:
                        # If trainer ID is not found in the session or database, redirect to main page
                        return redirect(url_for('main'))
                return render_template('client.html', role=user.role, trainer_id=trainer_id)  # Pass the role and trainer's ID to the template
    return redirect(url_for('login'))


@app.route('/add_client', methods=['GET', 'POST'])
def add_client():
    # Check if the user is logged in and get their username
    username = session.get('username')

    # Retrieve the trainer_id associated with this username from the session
    trainer_id = session.get('trainer_id')

    # Assuming you have a User model
    user = User.query.filter_by(username=username).first()

    # Fetch clients from the /fetch_clients route
    response = requests.get('http://localhost:5000/fetch_clients')  # Assuming the Flask app is running locally
    if response.status_code == 200:
        clients = response.json()  # Parse JSON response
    else:
        clients = []  # Handle error case

    # Pass the fetched data to the template
    return render_template('add_client.html', clients=clients, username=username, user=user, trainer_id=trainer_id)



@app.route('/assign_client_to_trainer', methods=['POST'])
def assign_client_to_trainer():
    if request.method == 'POST':
        # Retrieve trainer_id from the session
        trainer_id = request.form.get('trainer_id')
        
        # Retrieve client_id from the form
        client_id = request.form.get('client_id')

        # Perform validation if needed (e.g., check if trainer_id and client_id exist)

        # Assign the client to the trainer
        assignment = ClientTrainerAssignment(client_id=client_id, trainer_id=trainer_id)
        db.session.add(assignment)
        db.session.commit()

        # Redirect to a page indicating success or back to the add_client page
        return redirect(url_for('add_client'))

    # Handle other request methods if needed
    return redirect(url_for('add_client'))  # Redirect in case of a GET request

@app.route('/view_clients')
def view_clients():
    trainer_id = session.get('trainer_id')
    response = requests.get('http://localhost:5000/fetch_trainers_clients', params={'trainer_id': trainer_id})  # Use params instead of data
    if response.status_code == 200:
        clients = response.json()
    else:
        clients = []
    return render_template('view_clients.html', clients=clients, trainer_id=trainer_id)


def fetch_workout_programs():
    # Query the database to retrieve all workout programs
    workout_programs = WorkoutProgram.query.all()
    # Initialize an empty list to store the workout programs with their associated exercises
    workout_programs_with_exercises = []
    # Iterate through each workout program
    for workout in workout_programs:
        # Fetch the exercises associated with the current workout program
        exercises = Exercises.query.join(WorkoutProgramExercises).filter(WorkoutProgramExercises.workout_id == workout.workout_id).all()
        # Append the workout program along with its associated exercises to the list
        workout_programs_with_exercises.append({
            'workout': workout,
            'exercises': exercises
        })
    return workout_programs_with_exercises


def fetch_nutrition_programs():
    # Query the database to retrieve all nutrition programs
    nutrition_programs = NutritionProgram.query.all()
    # Initialize an empty list to store the nutrition programs with their associated food items
    nutrition_programs_with_food = []
    # Iterate through each nutrition program
    for nutrition in nutrition_programs:
        # Fetch the food items associated with the current nutrition program
        food_items = Food.query.join(FoodNutritionProgram).filter(FoodNutritionProgram.nutrition_program_id == nutrition.n_id).all()
        # Append the nutrition program along with its associated food items to the list
        nutrition_programs_with_food.append({
            'nutrition': nutrition,
            'food_items': food_items
        })
    return nutrition_programs_with_food




# @app.route('/assign_program_to_client/<int:client_id>', methods=['POST'])
# def assign_program_to_client(client_id):
#     # Retrieve the client object
#     client = Client.query.get_or_404(client_id)
#     # Fetch workout programs for display
#     workout_programs = WorkoutProgram.query.all()  # Assuming you have a WorkoutProgram model
#     if request.method == 'POST':
#         program_type = request.form.get('program_type')
        
#         # Retrieve the program_id based on the program_type
#         if program_type == 'workout':
#             program_id = request.form.get('program_with_exercises.workout_id')
#         else:
#             return jsonify({'error': 'Invalid program type'}), 400

#         # Check if the trainer_id is stored in the session
#         if 'trainer_id' in session:
#             trainer_id = session['trainer_id']
#         else:
#             # Handle the case where the trainer_id is not found in the session
#             return jsonify({'error': 'Trainer ID not found in session'}), 400

#         # Validate client_id
#         if not client:
#             return jsonify({'error': 'Invalid client ID'}), 400
        
#         if program_type != 'workout':
#             return jsonify({'error': 'Invalid program type'}), 400
        

#         assigned_program = AssignedWorkoutProgram(
#             workout_program_id=program_id,
#             client_id=client_id,
#             trainer_id=trainer_id
#         )
        
#         db.session.add(assigned_program)
#         db.session.commit()
        
#         return redirect(url_for('view_clients', client_id=client_id))
    
#     return render_template('assign_to_client.html', client=client, workout_programs=workout_programs)

@app.route('/assign_program_to_client/<int:client_id>', methods=['GET', 'POST'])
def assign_program_to_client(client_id):
    # Retrieve the client object
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'GET':
        # Fetch workout and nutrition programs for display
        nutrition_programs = NutritionProgram.query.all()

        workout_programs = WorkoutProgram.query.all()
        
        return render_template('assign_to_client.html', client=client, workout_programs=workout_programs, nutrition_programs=nutrition_programs)
    
    elif request.method == 'POST':
        program_type = request.form.get('program_type')
        
        if program_type == 'workout':
            return assign_workout_program(client_id)
        elif program_type == 'nutrition':
            return assign_nutrition_program(client_id)
        else:
            return jsonify({'error': 'Invalid program type'}), 400

def assign_workout_program(client_id):
    # Retrieve the client object
    client = Client.query.get_or_404(client_id)
    
    # Fetch workout programs for display
    workout_programs = WorkoutProgram.query.all()
        
    if request.method == 'POST':
        program_type = request.form.get('program_type')
        
        # Retrieve the program_id based on the program_type
        if program_type == 'workout':
            workout_id = request.form.get('program_id')
        else:
            return jsonify({'error': 'Invalid program type'}), 400

        # Check if the trainer_id is stored in the session
        if 'trainer_id' in session:
            trainer_id = session['trainer_id']
        else:
            # Handle the case where the trainer_id is not found in the session
            return jsonify({'error': 'Trainer ID not found in session'}), 400

        # Validate client_id
        if not client:
            return jsonify({'error': 'Invalid client ID'}), 400
        
        if program_type != 'workout':
            return jsonify({'error': 'Invalid program type'}), 400
        
        assigned_program = AssignedWorkoutProgram(
            workout_program_id=workout_id,
            client_id=client_id,
            trainer_id=trainer_id
        )
        
        db.session.add(assigned_program)
        db.session.commit()
        
        return redirect(url_for('view_clients', client_id=client_id))

def assign_nutrition_program(client_id):
    # Retrieve the client object
    client = Client.query.get_or_404(client_id)
    
    # Fetch nutrition programs for display
    nutrition_programs = NutritionProgram.query.all()
    
    nutrition_id = request.form.get('program_id')
    
    # Check if the trainer_id is stored in the session
    if 'trainer_id' in session:
        trainer_id = session['trainer_id']
    else:
        # Handle the case where the trainer_id is not found in the session
        return jsonify({'error': 'Trainer ID not found in session'}), 400

    # Validate client_id
    if not client:
        return jsonify({'error': 'Invalid client ID'}), 400
    
    assigned_program = AssignedNutritionProgram(
        nutrition_program_id=nutrition_id,
        client_id=client_id,
        trainer_id=trainer_id
    )
    
    db.session.add(assigned_program)
    db.session.commit()

    return redirect(url_for('view_clients', client_id=client_id))


@app.route('/fetch_trainers_clients')
def fetch_trainers_clients():
    trainer_id = request.args.get('trainer_id')
    tclients = Client.query.join(ClientTrainerAssignment).filter(ClientTrainerAssignment.trainer_id == trainer_id).all()
    tclient_data = [{'client_id': client.id, 'username': client.user.username, 'email': client.user.email} for client in tclients]
    return jsonify(tclient_data)

@app.route('/fetch_clients')
def fetch_clients():
    clients = Client.query.all()
    client_data = [{'client_id': client.id, 'username': client.user.username, 'email': client.user.email} for client in clients]
    return jsonify(client_data)

@app.route('/client_details/<int:client_id>')
def client_details(client_id):
    client = Client.query.get(client_id)
    if client:
        client_details = {'email': client.user.email}  # Add more client details as needed
        return jsonify(client_details)
    return jsonify({'error': 'Client not found'}), 404



@app.route('/delete_client/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    # Check if the request method is POST
    if request.method == 'POST':
        # Retrieve the client from the database
        client = Client.query.get(client_id)
        if client:
            # Delete the client from the database
            db.session.delete(client)
            db.session.commit()
            # Redirect to the view_clients page
            return redirect(url_for('view_clients'))
    # If the request method is not POST or client is not found, redirect to the view_clients page
    return redirect(url_for('view_clients'))


@app.route('/remove_client/<int:client_id>', methods=['POST'])
def remove_client(client_id):
    if request.method == 'POST':
        # Remove the client from assigned programs
        AssignedNutritionProgram.query.filter_by(client_id=client_id).delete()
        AssignedWorkoutProgram.query.filter_by(client_id=client_id).delete()
        # Commit changes to the database
        db.session.commit()
        # Redirect to the view_clients page
        return redirect(url_for('view_clients'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('homepage'))

if __name__ == "__main__":
    app.run(debug=True)

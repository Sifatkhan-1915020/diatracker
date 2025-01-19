from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Set this as an environment variable
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Set this as an environment variable
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(120))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    location = db.Column(db.String(120))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        name = request.form.get("name")
        height = request.form.get("height", type=float)
        weight = request.form.get("weight", type=float)
        location = request.form.get("location")

        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.")
            return redirect(url_for("signup"))

        new_user = User(username=username, password=password, name=name, height=height, weight=weight, location=location)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! You can now log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            flash("Logged in successfully!")
            if not user.name or not user.height or not user.weight or not user.location:
                return redirect(url_for("profile"))
            return redirect(url_for("home"))
        flash("Invalid credentials. Please try again.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!")
    return redirect(url_for("login"))

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if not user.name or not user.height or not user.weight or not user.location:
        return redirect(url_for("profile"))
    return render_template("index.html", user=user)

@app.route("/send_profile", methods=["POST"])
def send_profile():
    if "user_id" not in session:
        flash("Please log in to send your profile.")
        return redirect(url_for("login"))

    recipient_email = request.form["email"]
    user = User.query.get(session["user_id"])

    if user and recipient_email:
        try:
            # Construct the email message
            msg = Message("Your DiaTracker Profile", recipients=[recipient_email])
            msg.body = f"""
            Hello,

            Here are the profile details of {user.username}:

            Name: {user.name or "N/A"}
            Height: {user.height or "N/A"} cm
            Weight: {user.weight or "N/A"} kg
            Location: {user.location or "N/A"}

            Best regards,
            DiaTracker Team
            """
            mail.send(msg)
            flash("Profile sent successfully!")
        except Exception as e:
            flash(f"Error sending email: {e}")
    else:
        flash("Invalid email or user profile.")

    return redirect(url_for("home"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Please log in to access your profile.")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        user.name = request.form["name"]
        user.height = request.form["height"]
        user.weight = request.form["weight"]
        user.location = request.form["location"]
        db.session.commit()
        flash("Profile updated successfully!")
        return redirect(url_for("home"))

    return render_template("profile.html", user=user)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure the database is created
    app.run(debug=True)

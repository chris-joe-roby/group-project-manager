from flask import Flask, jsonify, render_template
from backend.models import db, Student
from backend.services.grouping_service import get_students, create_groups, save_groups

app = Flask(__name__)

# ---------------- DATABASE CONFIG ----------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

    # Insert demo students if empty
    if Student.query.count() == 0:
        demo_students = [
            "Alice", "Bob", "Charlie", "David",
            "Emma", "Frank", "Grace", "Helen",
            "Ibrahim", "John", "Kevin", "Liya"
        ]

        for name in demo_students:
            db.session.add(Student(name=name))

        db.session.commit()
        print("Demo students inserted!")


# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- API ----------------
@app.route("/api/generate-groups", methods=["POST"])
def generate_groups_api():
    students = get_students()
    groups = create_groups(students, 4)
    save_groups(groups)

    return jsonify({
        "message": "Groups created successfully",
        "groups": groups
    })


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)
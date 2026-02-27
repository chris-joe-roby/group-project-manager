from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Students table
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

# Group table
class ProjectGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)

# Members inside each group
class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    group_id = db.Column(db.Integer, db.ForeignKey('project_group.id'))
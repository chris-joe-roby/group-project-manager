from backend.models import db, Student, ProjectGroup, GroupMember


def get_students():
    students = Student.query.all()
    names = [s.name for s in students]
    print("STUDENTS:", names)
    return names


def create_groups(students, group_size=4):
    groups = []
    for i in range(0, len(students), group_size):
        groups.append(students[i:i+group_size])

    print("GROUPS:", groups)
    return groups


def save_groups(groups):
    # clear old groups
    GroupMember.query.delete()
    ProjectGroup.query.delete()

    for group in groups:
        new_group = ProjectGroup()
        db.session.add(new_group)
        db.session.flush()

        for member in group:
            db.session.add(GroupMember(
                student_name=member,
                group_id=new_group.id
            ))

    db.session.commit()
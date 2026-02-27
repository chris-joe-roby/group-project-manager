import json
import os
from collections import Counter
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "profiles.json")
MONTHLY_GOAL = 30


def _load_profiles():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_profiles(profiles):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(profiles, file, indent=2)


def _parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        skills = request.form.get("skills", "").strip()
        role = request.form.get("role", "").strip()

        if not name or not email or not skills or not role:
            error = "Please complete all fields before submitting."
            return render_template(
                "profile.html",
                error=error,
                is_edit=False,
                form_data={
                    "name": name,
                    "email": email,
                    "skills": skills,
                    "role": role,
                },
            )

        profiles = _load_profiles()
        if any(p["email"] == email for p in profiles):
            error = "A profile with this email already exists."
            return render_template(
                "profile.html",
                error=error,
                is_edit=False,
                form_data={
                    "name": name,
                    "email": email,
                    "skills": skills,
                    "role": role,
                },
            )

        profiles.append(
            {
                "name": name,
                "email": email,
                "skills": skills,
                "role": role,
                "submitted_at": datetime.utcnow().isoformat() + "Z",
            }
        )
        _save_profiles(profiles)
        return redirect(url_for("view_profiles"))

    return render_template("profile.html", form_data={}, is_edit=False)


@app.route("/edit", methods=["GET", "POST"])
def edit_profile():
    if request.method == "POST":
        original_email = request.form.get("original_email", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        skills = request.form.get("skills", "").strip()
        role = request.form.get("role", "").strip()

        if not original_email or not name or not email or not skills or not role:
            error = "Please complete all fields before saving."
            return render_template(
                "profile.html",
                error=error,
                is_edit=True,
                form_data={
                    "name": name,
                    "email": email,
                    "skills": skills,
                    "role": role,
                    "original_email": original_email,
                },
            )

        profiles = _load_profiles()
        profile_index = next(
            (index for index, profile in enumerate(profiles) if profile["email"] == original_email),
            None,
        )

        if profile_index is None:
            return redirect(url_for("view_profiles"))

        if email != original_email and any(p["email"] == email for p in profiles):
            error = "Another profile with this email already exists."
            return render_template(
                "profile.html",
                error=error,
                is_edit=True,
                form_data={
                    "name": name,
                    "email": email,
                    "skills": skills,
                    "role": role,
                    "original_email": original_email,
                },
            )

        profiles[profile_index].update(
            {
                "name": name,
                "email": email,
                "skills": skills,
                "role": role,
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
        )

        _save_profiles(profiles)
        return redirect(url_for("view_profiles"))

    email = request.args.get("email", "").strip()
    profiles = _load_profiles()
    profile_data = next((profile for profile in profiles if profile["email"] == email), None)

    if not profile_data:
        return redirect(url_for("view_profiles"))

    return render_template(
        "profile.html",
        form_data={
            "name": profile_data.get("name", ""),
            "email": profile_data.get("email", ""),
            "skills": profile_data.get("skills", ""),
            "role": profile_data.get("role", ""),
            "original_email": profile_data.get("email", ""),
        },
        is_edit=True,
    )


@app.route("/delete", methods=["POST"])
def delete_profile():
    email = request.form.get("email")

    profiles = _load_profiles()
    profiles = [p for p in profiles if p["email"] != email]

    _save_profiles(profiles)

    return redirect(url_for("view_profiles"))

@app.route("/profiles")
def view_profiles():
    profiles = _load_profiles()

    role_counter = Counter(profile.get("role", "Unknown") for profile in profiles)
    total_coders = sum(
        1 for profile in profiles if "coder" in profile.get("role", "").strip().lower()
    )
    backend_coders = sum(
        1
        for profile in profiles
        if profile.get("role", "").strip().lower() == "coder (backend)"
    )
    frontend_coders = sum(
        1
        for profile in profiles
        if profile.get("role", "").strip().lower() == "coder (frontend)"
    )

    top_skills = Counter()
    for profile in profiles:
        skills = profile.get("skills", "")
        for skill in skills.split(","):
            skill_name = skill.strip()
            if skill_name:
                top_skills[skill_name] += 1

    top_skill_items = top_skills.most_common(10)
    max_skill_count = top_skill_items[0][1] if top_skill_items else 1
    skill_stats = [
        {
            "name": skill_name,
            "count": count,
            "percentage": int((count / max_skill_count) * 100),
        }
        for skill_name, count in top_skill_items
    ]

    today = datetime.now(timezone.utc).date()
    last_7_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    submissions_by_day = {day: 0 for day in last_7_days}

    for profile in profiles:
        submitted_dt = _parse_iso_datetime(profile.get("submitted_at"))
        if submitted_dt:
            submitted_date = submitted_dt.date()
            if submitted_date in submissions_by_day:
                submissions_by_day[submitted_date] += 1

    submission_labels = [day.strftime("%b %d") for day in last_7_days]
    submission_values = [submissions_by_day[day] for day in last_7_days]

    current_month_count = 0
    for profile in profiles:
        submitted_dt = _parse_iso_datetime(profile.get("submitted_at"))
        if submitted_dt and submitted_dt.year == today.year and submitted_dt.month == today.month:
            current_month_count += 1

    monthly_progress = min(int((current_month_count / MONTHLY_GOAL) * 100), 100)

    recent_profiles = sorted(
        profiles,
        key=lambda profile: profile.get("submitted_at", ""),
        reverse=True,
    )[:5]

    chart_role_labels = list(role_counter.keys())
    chart_role_values = list(role_counter.values())

    return render_template(
        "profiles.html",
        profiles=profiles,
        total_coders=total_coders,
        backend_coders=backend_coders,
        frontend_coders=frontend_coders,
        role_counter=role_counter,
        chart_role_labels=chart_role_labels,
        chart_role_values=chart_role_values,
        submission_labels=submission_labels,
        submission_values=submission_values,
        skill_stats=skill_stats,
        recent_profiles=recent_profiles,
        current_month_count=current_month_count,
        monthly_goal=MONTHLY_GOAL,
        monthly_progress=monthly_progress,
    )


@app.route("/profile-detail")
def profile_detail():
    email = request.args.get("email", "").strip()
    profiles = _load_profiles()
    profile_data = next((profile for profile in profiles if profile["email"] == email), None)

    if not profile_data:
        return redirect(url_for("view_profiles"))

    return render_template("profile_detail.html", profile=profile_data)

if __name__ == "__main__":
    app.run(debug=True)
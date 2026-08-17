from flask import Blueprint, render_template

ui_bp = Blueprint('ui', __name__)

@ui_bp.route("/")
def home():
    return render_template("index.html")

@ui_bp.route("/login")
def login():
    return render_template("login.html")

@ui_bp.route("/signup")
def signup():
    return render_template("signup.html")

@ui_bp.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

@ui_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@ui_bp.route("/plant")
def plant():
    return render_template("plant.html")

@ui_bp.route("/analytics")
def analytics():
    return render_template("analytics.html")

@ui_bp.route("/community")
def community():
    return render_template("community.html")

@ui_bp.route("/marketplace")
def marketplace():
    return render_template("marketplace.html")

@ui_bp.route("/report/<int:report_id>")
def view_report(report_id):
    from models.plant import HealthReport
    report = HealthReport.query.get_or_404(report_id)
    return render_template("report.html", report=report)

"""
analytics_routes.py — Plant health analytics, trends, and disease alerts.
"""
from flask import Blueprint, jsonify, session
from database.extensions import db
from models.plant import Plant, HealthReport, WeeklyPhoto, PlantSchedule
from models.user import User
from datetime import datetime, timedelta

from routes.auth import get_authenticated_user

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route("/api/analytics/summary", methods=["GET"])
@analytics_bp.route("/api/analytics/<int:user_id>", methods=["GET"])
def get_analytics(user_id=None):
    """
    Return comprehensive analytics data for the authenticated user, matching SaaS UI requirements.
    Includes: summary, health trends, disease distribution, watering consistency, tasks, and AI insights.
    """
    user = get_authenticated_user()
    # FIX: also accept Bearer token (same as all other endpoints)
    if not user:
        from flask import request as _req
        auth_header = _req.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            uid = auth_header.split(" ")[1]
            user = User.query.get(uid)
    if not user or (user_id is not None and user.id != user_id):
        return jsonify({"error": "Unauthorized"}), 401
    
    # If using the summary alias without a user_id, use the auth user's ID
    if user_id is None:
        user_id = user.id

    plants = Plant.query.filter_by(user_id=user_id).all()
    if not plants:
        return jsonify({
            "success": True, "has_data": False, "total_plants": 0, "healthy_plants": 0, "diseased_plants": 0, "avg_health_score": 0, "total_scans": 0,
            "summary": {"plant_count": 0, "healthy_count": 0, "sick_count": 0, "avg_health": 0, "total_scans": 0, "tasks_completed": 0, "last_scan_time": "Never"},
            "health_trend": {"labels": [], "scores": []},
            "disease_distribution": {},
            "watering_history": {"labels": [], "data": []},
            "task_analytics": {"completed": 0, "missed": 0, "percentage": 0},
            "growth_progress": [],
            "scan_activity": {"labels": [], "data": []},
            "ai_insights": "Add some plants to your garden to start seeing AI insights!"
        })

    plant_ids = [p.id for p in plants]
    from models.plant import CareTask

    # 1. Summary Stats
    healthy_count = sum(1 for p in plants if (p.health_score or 0) >= 80)
    sick_count    = sum(1 for p in plants if (p.health_score or 0) < 60)
    avg_health    = int(sum(p.health_score or 0 for p in plants) / len(plants)) if plants else 0
    total_scans   = HealthReport.query.filter(HealthReport.plant_id.in_(plant_ids)).count() if plant_ids else 0
    total_tasks_completed = CareTask.query.filter(CareTask.plant_id.in_(plant_ids), CareTask.is_completed == True).count() if plant_ids else 0
    
    last_scan = HealthReport.query.filter(HealthReport.plant_id.in_(plant_ids)).order_by(HealthReport.created_at.desc()).first()
    last_scan_time = last_scan.created_at.strftime("%b %d, %H:%M") if last_scan and last_scan.created_at else "No scans yet"

    # 2. Health Trend (last 8 weeks)
    now = datetime.utcnow()
    week_labels = []
    week_scores = []
    for i in range(7, -1, -1):
        week_start = now - timedelta(weeks=i+1)
        week_end   = now - timedelta(weeks=i)
        week_labels.append((now - timedelta(weeks=i)).strftime("%b %d"))
        
        photos_in_week = WeeklyPhoto.query.filter(
            WeeklyPhoto.plant_id.in_(plant_ids),
            WeeklyPhoto.created_at >= week_start,
            WeeklyPhoto.created_at < week_end,
            (WeeklyPhoto.is_diagnosis == False) | (WeeklyPhoto.is_diagnosis == None)
        ).all()
        
        avg = int(sum(p.health_score or 0 for p in photos_in_week) / len(photos_in_week)) if photos_in_week else avg_health
        week_scores.append(avg)

    # 3. Disease Distribution (Pie Chart)
    disease_counts = {"Healthy": healthy_count}
    for p in plants:
        if p.status != "Healthy" and p.last_disease:
            curr = disease_counts.get(p.last_disease, 0)
            disease_counts[p.last_disease] = curr + 1

    # 4. Watering Consistency (using WaterLog - last 7 days)
    from models.plant import WaterLog
    watering_labels = []
    watering_data = []
    unique_days_watered = 0
    
    # We look at the last 7 days including today
    for i in range(6, -1, -1):
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        watering_labels.append(day_start.strftime("%a"))
        
        count = 0
        if plant_ids:
            count = WaterLog.query.filter(
                WaterLog.plant_id.in_(plant_ids),
                WaterLog.watered_at >= day_start,
                WaterLog.watered_at < day_end
            ).count()
            
            if count > 0:
                unique_days_watered += 1
                
        watering_data.append(count)

    water_consistency = int((unique_days_watered / 7) * 100)
    print(f"[GROWZEN] Water consistency debug: logs found in {unique_days_watered} of last 7 days. Consistency: {water_consistency}%")


    # 5. Care Task Analytics (This Week)
    week_ago = now - timedelta(days=7)
    tasks_this_week_completed = 0
    tasks_this_week_missed = 0
    if plant_ids:
        all_week_tasks = CareTask.query.filter(
            CareTask.plant_id.in_(plant_ids),
            CareTask.created_at >= week_ago
        ).all()
        for t in all_week_tasks:
            if t.is_completed: tasks_this_week_completed += 1
            else: tasks_this_week_missed += 1
            
    total_week_tasks = max(1, len(all_week_tasks)) if plant_ids else 1
    task_completion_pct = int((tasks_this_week_completed / total_week_tasks) * 100)

    # 6. Plant Growth Progress
    growth_data = [{"name": p.name, "stage": p.growth_stage or "Seedling", "health": p.health_score or 0} for p in plants]

    # 7. Scan Activity (Scans per week - last 4 weeks)
    scan_labels = []
    scan_counts = []
    for i in range(3, -1, -1):
        week_start = now - timedelta(weeks=i+1)
        week_end = now - timedelta(weeks=i)
        scan_labels.append(f"Week {4-i}")
        if plant_ids:
            count = HealthReport.query.filter(
                HealthReport.plant_id.in_(plant_ids),
                HealthReport.created_at >= week_start,
                HealthReport.created_at < week_end
            ).count()
        else: count = 0
        scan_counts.append(count)

    # 8. AI Insights Generation via Groq — wrapped so a timeout doesn't crash the page
    ai_insights = f"Your garden maintains an average health of {avg_health}%. You completed {task_completion_pct}% of tasks this week."
    try:
        from services.chatbot.groqService import generate_chat_response
        prompt_context = (
            f"User Garden Context: {len(plants)} total plants. {healthy_count} healthy. "
            f"Average health score is {avg_health}%. Disease distribution: {disease_counts}. "
            f"They completed {tasks_this_week_completed} tasks this week ({task_completion_pct}% completion rate). "
            f"Generate 2 extremely concise, professional SaaS-style insight sentences about their garden performance based ONLY on this data."
        )
        ai_result = generate_chat_response(prompt_context)
        if ai_result and not ai_result.startswith("AI Error"):
            ai_insights = ai_result
    except Exception as groq_err:
        print(f"[GROWZEN] Groq insights skipped (non-critical): {groq_err}")

    print(f"[GROWZEN] Analytics result: plants={len(plants)}, avg_health={avg_health}, scans={total_scans}")

    return jsonify({
        "success": True,
        "has_data": True,
        # flat summary (spec requires these at top level too)
        "total_plants":    len(plants),
        "healthy_plants":  healthy_count,
        "diseased_plants": sick_count,
        "avg_health_score": avg_health,
        "total_scans":     total_scans,
        "last_scan_time":  last_scan_time,
        "water_consistency": water_consistency,
        # nested summary (analytics.js reads this)
        "summary": {
            "plant_count":      len(plants),
            "healthy_count":    healthy_count,
            "sick_count":       sick_count,
            "avg_health":       avg_health,
            "total_scans":      total_scans,
            "tasks_completed":  total_tasks_completed,
            "last_scan_time":   last_scan_time,
            "water_consistency": water_consistency
        },
        "health_trend": {
            "labels": week_labels,
            "scores": week_scores
        },
        "disease_distribution": disease_counts,
        "watering_history": {
            "labels": watering_labels,
            "data": watering_data
        },
        "task_analytics": {
            "completed":  tasks_this_week_completed,
            "missed":     tasks_this_week_missed,
            "percentage": task_completion_pct
        },
        "growth_progress": growth_data,
        "scan_activity": {
            "labels": scan_labels,
            "data": scan_counts
        },
        "ai_insights": ai_insights
    })


@analytics_bp.route("/api/analytics/<int:user_id>/plants", methods=["GET"])
def get_plant_analytics(user_id):
    """Per-plant analytics breakdown."""
    user = get_authenticated_user()
    if not user or user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 401

    plants = Plant.query.filter_by(user_id=user_id).all()
    result = []
    for p in plants:
        photos = WeeklyPhoto.query.filter_by(plant_id=p.id).filter(
            (WeeklyPhoto.is_diagnosis == False) | (WeeklyPhoto.is_diagnosis == None)
        ).order_by(WeeklyPhoto.created_at.asc()).all()

        score_trend = [ph.health_score or 0 for ph in photos[-6:]] if photos else [p.health_score or 0]
        
        result.append({
            "id":           p.id,
            "name":         p.name,
            "status":       p.status,
            "health_score": p.health_score or 0,
            "disease":      p.last_disease,
            "photo_count":  len(photos),
            "score_trend":  score_trend,
            "last_scanned": p.last_scanned.strftime("%b %d") if p.last_scanned else "Never"
        })

    return jsonify(result)

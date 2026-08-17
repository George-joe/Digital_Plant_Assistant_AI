"""
community.py — Community feed, leaderboard, XP system, and Marketplace stub.
"""
from flask import Blueprint, request, jsonify, session, current_app
from utils.helpers import get_authenticated_user
from database.extensions import db
from models.community import CommunityPost, PostLike, PostComment
from models.user import User
from models.plant import Plant
import os

community_bp = Blueprint('community', __name__)


# ─── XP / LEVEL SYSTEM ─────────────────────────────────────────────────────

XP_LEVEL_THRESHOLDS = [
    (0,    "🌱 Seedling"),
    (100,  "🌿 Sprout"),
    (300,  "🪴 Gardener"),
    (700,  "🌳 Plant Expert"),
    (1500, "🏆 Master Grower"),
]


def xp_to_level(xp: int) -> str:
    level = XP_LEVEL_THRESHOLDS[0][1]
    for threshold, name in XP_LEVEL_THRESHOLDS:
        if xp >= threshold:
            level = name
    return level


def xp_for_next_level(xp: int) -> dict:
    for i, (threshold, name) in enumerate(XP_LEVEL_THRESHOLDS):
        if xp < threshold:
            prev = XP_LEVEL_THRESHOLDS[i - 1][0] if i > 0 else 0
            return {"next_level": name, "needed": threshold, "current": xp, "prev": prev}
    return {"next_level": "Max Level", "needed": xp, "current": xp, "prev": XP_LEVEL_THRESHOLDS[-1][0]}


def award_xp(user_id: int, points: int):
    """Award XP to a user and sync their level label."""
    user = User.query.get(user_id)
    if not user:
        return
    user.xp_points = (user.xp_points or 0) + points
    user.level = xp_to_level(user.xp_points)
    db.session.commit()


def get_user_badges(user) -> list:
    badges = []
    plant_count = Plant.query.filter_by(user_id=user.id).count()
    if plant_count >= 1:
        badges.append("First Plant 🌱")
    if plant_count >= 10:
        badges.append("Plant Lover 🌿")
    if (user.xp_points or 0) >= 1500:
        badges.append("Master Grower 🏆")
    if (user.streak_days or 0) >= 7:
        badges.append("Weekly Tracker 📅")
    if CommunityPost.query.filter_by(user_id=user.id).count() >= 5:
        badges.append("Community Helper 💬")
    return badges


# ─── COMMUNITY FEED ─────────────────────────────────────────────────────────

@community_bp.route("/api/community/feed", methods=["GET"])
def get_feed():
    posts = CommunityPost.query.order_by(CommunityPost.created_at.desc()).all()
    user = get_authenticated_user()
    user_id = user.id if user else None
    feed = []
    for p in posts:
        author = User.query.get(p.user_id)
        if not author:
            continue
        user_liked = bool(user_id and PostLike.query.filter_by(post_id=p.id, user_id=user_id).first())
        feed.append({
            "id": p.id,
            "user": author.name,
            "user_id": p.user_id,
            "level": author.level,
            "content": p.content,
            "image_url": p.image_url,
            "likes": p.likes_count,
            "comments": PostComment.query.filter_by(post_id=p.id).count(),
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M"),
            "user_liked": user_liked,
        })
    return jsonify({"success": True, "data": feed})


@community_bp.route("/api/community/post", methods=["POST"])
def create_post():
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user.id
    content = request.form.get("content")
    current_app.logger.info(f"Received Community Post request from user_id {user_id}")
    if not content:
        return jsonify({"error": "Content is required"}), 400

    image_url = None
    if "image" in request.files:
        f = request.files["image"]
        if f.filename:
            import uuid
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "jpg"
            unique_name = f"community_{uuid.uuid4().hex}.{ext}"
            folder = current_app.config.get("UPLOAD_FOLDER", "static/uploads")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, unique_name)
            f.save(path)
            image_url = f"/static/uploads/{unique_name}"

    post = CommunityPost(user_id=user_id, content=content, image_url=image_url)
    db.session.add(post)
    db.session.commit()
    current_app.logger.info(f"Database commit successful for post {post.id}")
    award_xp(user_id, 10)
    return jsonify({"success": True, "post_id": post.id})


@community_bp.route("/api/community/post/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    """Delete a community post — only the author can delete their own post."""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    post = CommunityPost.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    if post.user_id != user.id:
        return jsonify({"error": "You can only delete your own posts"}), 403
    # Also delete likes and comments
    PostLike.query.filter_by(post_id=post_id).delete()
    PostComment.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    return jsonify({"success": True})


@community_bp.route("/api/community/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user.id
    post = CommunityPost.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    like = PostLike.query.filter_by(post_id=post_id, user_id=user_id).first()
    if like:
        db.session.delete(like)
        post.likes_count -= 1
        liked = False
    else:
        db.session.add(PostLike(post_id=post_id, user_id=user_id))
        post.likes_count += 1
        liked = True
    db.session.commit()
    return jsonify({"success": True, "likes": post.likes_count, "liked": liked})


# ─── LEADERBOARD ─────────────────────────────────────────────────────────────

@community_bp.route("/api/community/leaderboard")
def leaderboard():
    users = User.query.order_by(User.xp_points.desc()).limit(50).all()
    result = []
    for rank, u in enumerate(users, 1):
        plants = Plant.query.filter_by(user_id=u.id).all()
        avg_health = round(
            sum(p.health_score or 0 for p in plants) / len(plants)
        ) if plants else 0

        xp = u.xp_points or 0
        nxt = xp_for_next_level(xp)
        # Compute progress %
        span = nxt["needed"] - nxt["prev"]
        progress = round(((xp - nxt["prev"]) / span) * 100) if span > 0 else 100

        result.append({
            "rank": rank,
            "id": u.id,
            "name": u.name,
            "level": u.level or "🌱 Seedling",
            "xp": xp,
            "plants": len(plants),
            "avg_health": avg_health,
            "streak": u.streak_days or 0,
            "badges": get_user_badges(u),
            "next_level": nxt["next_level"],
            "xp_progress": min(progress, 100),
        })
    return jsonify({"success": True, "data": result})


@community_bp.route("/api/community/xp", methods=["POST"])
def give_xp():
    """Award XP via API — used by game events."""
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user.id
    body = request.get_json(silent=True) or {}
    pts = int(body.get("points", 0))
    if pts > 0:
        award_xp(user_id, pts)
    return jsonify({"success": True})


# ─── MARKETPLACE STUB ────────────────────────────────────────────────────────

@community_bp.route("/api/marketplace/items", methods=["GET"])
def get_marketplace():
    return jsonify([
        {"id": 1, "item": "Premium Indoor Soil Mix",  "price": "$12.99", "seller": "@GrowZenOfficial"},
        {"id": 2, "item": "Liquid Plant Fertilizer",   "price": "$9.99",  "seller": "@GreenThumb"},
        {"id": 3, "item": "Monstera Seeds (10-pack)",  "price": "$5.50",  "seller": "@SeedBankHQ"},
        {"id": 4, "item": "Terracotta Pot (8 inch)",   "price": "$14.00", "seller": "@CeramicArts"},
    ])

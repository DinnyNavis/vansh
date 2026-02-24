"""
Project CRUD Routes — Create, list, get, update, delete projects.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from ..models import ProjectModel

projects_bp = Blueprint("projects", __name__)


def _serialize_project(project_in):
    """Convert MongoDB document to JSON-serializable dict and scrub broken URLs."""
    if not project_in:
        return None
    
    # Create a copy to prevent in-place mutation if from MockDB
    project = project_in.copy()
    
    project["_id"] = str(project["_id"])
    project["user_id"] = str(project["user_id"])
    
    # Scrub broken Pollinations URLs to prevent browser console errors
    if "chapters" in project:
        for chapter in project["chapters"]:
            url = chapter.get("image_url")
            if url and "pollinations.ai" in url:
                chapter["image_url"] = None

    if project.get("created_at") and hasattr(project["created_at"], "isoformat"):
        project["created_at"] = project["created_at"].isoformat()
    if project.get("updated_at") and hasattr(project["updated_at"], "isoformat"):
        project["updated_at"] = project["updated_at"].isoformat()
    return project


@projects_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    """Create a new project."""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    title = data.get("title", "Untitled Story").strip()
    input_type = data.get("input_type", "audio")

    if input_type not in ("audio", "text", "video", "upload-audio"):
        return jsonify({"error": "Invalid input type"}), 400

    project = ProjectModel.create(user_id, title, input_type)

    return jsonify({
        "message": "Project created",
        "project": _serialize_project(project),
    }), 201


@projects_bp.route("", methods=["GET"])
@jwt_required()
def list_projects():
    """List all projects for the current user."""
    user_id = get_jwt_identity()
    projects = ProjectModel.find_by_user(user_id)

    return jsonify({
        "projects": [_serialize_project(p) for p in projects],
    }), 200


@projects_bp.route("/<project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    """Get a specific project."""
    user_id = get_jwt_identity()

    try:
        project = ProjectModel.find_by_id(project_id)
    except Exception:
        return jsonify({"error": "Invalid project ID"}), 400

    if not project:
        return jsonify({"error": "Project not found"}), 404

    if str(project["user_id"]) != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({"project": _serialize_project(project)}), 200


@projects_bp.route("/<project_id>", methods=["PUT"])
@jwt_required()
def update_project(project_id):
    """Update a project (chapters, title, etc.)."""
    user_id = get_jwt_identity()
    data = request.get_json()

    try:
        project = ProjectModel.find_by_id(project_id)
    except Exception:
        return jsonify({"error": "Invalid project ID"}), 400

    if not project:
        return jsonify({"error": "Project not found"}), 404

    if str(project["user_id"]) != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    # Allowed update fields
    allowed = {
        "title", "cover_title", "cover_subtitle",
        "chapters", "transcript", "refined_text", "status",
    }
    update_data = {k: v for k, v in data.items() if k in allowed}

    if update_data:
        ProjectModel.update(project_id, update_data)

    updated = ProjectModel.find_by_id(project_id)
    return jsonify({
        "message": "Project updated",
        "project": _serialize_project(updated),
    }), 200


@projects_bp.route("/<project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    """Delete a project."""
    user_id = get_jwt_identity()

    try:
        project = ProjectModel.find_by_id(project_id)
    except Exception:
        return jsonify({"error": "Invalid project ID"}), 400

    if not project:
        return jsonify({"error": "Project not found"}), 404

    if str(project["user_id"]) != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    ProjectModel.delete(project_id)
    return jsonify({"message": "Project deleted"}), 200

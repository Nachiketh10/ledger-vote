"""
Every API response follows one of these shapes, so the frontend can
handle responses uniformly:

Success: { "success": true, "message": "...", "data": {...} }
Error:   { "success": false, "message": "...", "errors": {...} }
"""

from flask import jsonify


def success(data=None, message: str = "OK", status: int = 200):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def error(message: str = "An error occurred", status: int = 400, errors=None):
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return jsonify(payload), status

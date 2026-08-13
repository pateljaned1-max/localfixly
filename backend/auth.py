import datetime
import jwt
from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRES_HOURS

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return check_password_hash(hashed, password)

def create_jwt_token(user_id: int, role: str, email: str, name: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "name": name,
        "exp": now + datetime.timedelta(hours=JWT_EXPIRES_HOURS),
        "iat": now
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if "sub" in payload:
            payload["sub"] = int(payload["sub"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def get_current_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    return decode_jwt_token(token)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized. Please log in."}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated

def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Unauthorized. Token missing or invalid."}), 401
            if user.get("role") not in roles:
                return jsonify({
                    "error": f"Forbidden. Access requires one of the following roles: {', '.join(roles)}",
                    "required_roles": roles,
                    "user_role": user.get("role")
                }), 403
            request.current_user = user
            return f(*args, **kwargs)
        return decorated
    return decorator

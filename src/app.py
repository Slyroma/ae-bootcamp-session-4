"""
Slalom Capabilities Management System API

A FastAPI application that enables Slalom consultants to register their
capabilities and manage consulting expertise across the organization.
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import secrets

app = FastAPI(title="Slalom Capabilities Management API",
              description="API for managing consulting capabilities and consultant expertise")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


class LoginRequest(BaseModel):
    username: str
    password: str


class PracticeLeadStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.users = self._load_users()

    def _load_users(self):
        if not self.file_path.exists():
            return {}

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        users = {}
        for user in data.get("practice_leads", []):
            username = user.get("username")
            password_hash = user.get("password_hash")
            if username and password_hash:
                users[username] = user

        return users

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            salt_hex, digest_hex = password_hash.split(":")
            salt = binascii.unhexlify(salt_hex)
            expected_digest = binascii.unhexlify(digest_hex)
        except (ValueError, binascii.Error):
            return False

        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200000,
        )
        return secrets.compare_digest(actual_digest, expected_digest)

    def authenticate(self, username: str, password: str):
        user = self.users.get(username)
        if not user:
            return None

        if not self.verify_password(password, user["password_hash"]):
            return None

        return {
            "username": user["username"],
            "role": user.get("role", "practice_lead"),
            "practice_areas": user.get("practice_areas", []),
        }


practice_lead_store = PracticeLeadStore(current_dir / "practice_leads.json")
audit_logger = logging.getLogger("uvicorn.error")
session_lifetime = timedelta(hours=8)
active_sessions = {}


def log_audit_event(
    event: str,
    username: str,
    capability_name: str = "-",
    email: str = "-",
):
    audit_logger.info(
        "event=%s username=%s capability=%s consultant=%s",
        event,
        username,
        capability_name,
        email,
    )


def get_current_user(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "", 1).strip()
    session = active_sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    if datetime.now(timezone.utc) >= session["expires_at"]:
        active_sessions.pop(token, None)
        log_audit_event("session_expired", session["user"]["username"])
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return session["user"]


def require_practice_lead(authorization: str | None):
    user = get_current_user(authorization)
    if user.get("role") != "practice_lead":
        log_audit_event("authorization_denied", user["username"])
        raise HTTPException(status_code=403, detail="Practice lead access required")

    return user


def require_practice_area(user: dict, capability_name: str):
    practice_area = capabilities[capability_name]["practice_area"]
    if practice_area not in user.get("practice_areas", []):
        log_audit_event("authorization_denied", user["username"], capability_name)
        raise HTTPException(
            status_code=403,
            detail=f"Practice lead access to {practice_area} is required",
        )

# In-memory capabilities database
capabilities = {
    "Cloud Architecture": {
        "description": "Design and implement scalable cloud solutions using AWS, Azure, and GCP",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["AWS Solutions Architect", "Azure Architect Expert"],
        "industry_verticals": ["Healthcare", "Financial Services", "Retail"],
        "capacity": 40,  # hours per week available across team
        "consultants": ["alice.smith@slalom.com", "bob.johnson@slalom.com"]
    },
    "Data Analytics": {
        "description": "Advanced data analysis, visualization, and machine learning solutions",
        "practice_area": "Technology", 
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Tableau Desktop Specialist", "Power BI Expert", "Google Analytics"],
        "industry_verticals": ["Retail", "Healthcare", "Manufacturing"],
        "capacity": 35,
        "consultants": ["emma.davis@slalom.com", "sophia.wilson@slalom.com"]
    },
    "DevOps Engineering": {
        "description": "CI/CD pipeline design, infrastructure automation, and containerization",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"], 
        "certifications": ["Docker Certified Associate", "Kubernetes Admin", "Jenkins Certified"],
        "industry_verticals": ["Technology", "Financial Services"],
        "capacity": 30,
        "consultants": ["john.brown@slalom.com", "olivia.taylor@slalom.com"]
    },
    "Digital Strategy": {
        "description": "Digital transformation planning and strategic technology roadmaps",
        "practice_area": "Strategy",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Digital Transformation Certificate", "Agile Certified Practitioner"],
        "industry_verticals": ["Healthcare", "Financial Services", "Government"],
        "capacity": 25,
        "consultants": ["liam.anderson@slalom.com", "noah.martinez@slalom.com"]
    },
    "Change Management": {
        "description": "Organizational change leadership and adoption strategies",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Prosci Certified", "Lean Six Sigma Black Belt"],
        "industry_verticals": ["Healthcare", "Manufacturing", "Government"],
        "capacity": 20,
        "consultants": ["ava.garcia@slalom.com", "mia.rodriguez@slalom.com"]
    },
    "UX/UI Design": {
        "description": "User experience design and digital product innovation",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Adobe Certified Expert", "Google UX Design Certificate"],
        "industry_verticals": ["Retail", "Healthcare", "Technology"],
        "capacity": 30,
        "consultants": ["amelia.lee@slalom.com", "harper.white@slalom.com"]
    },
    "Cybersecurity": {
        "description": "Information security strategy, risk assessment, and compliance",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["CISSP", "CISM", "CompTIA Security+"],
        "industry_verticals": ["Financial Services", "Healthcare", "Government"],
        "capacity": 25,
        "consultants": ["ella.clark@slalom.com", "scarlett.lewis@slalom.com"]
    },
    "Business Intelligence": {
        "description": "Enterprise reporting, data warehousing, and business analytics",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Microsoft BI Certification", "Qlik Sense Certified"],
        "industry_verticals": ["Retail", "Manufacturing", "Financial Services"],
        "capacity": 35,
        "consultants": ["james.walker@slalom.com", "benjamin.hall@slalom.com"]
    },
    "Agile Coaching": {
        "description": "Agile transformation and team coaching for scaled delivery",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Certified Scrum Master", "SAFe Agilist", "ICAgile Certified"],
        "industry_verticals": ["Technology", "Financial Services", "Healthcare"],
        "capacity": 20,
        "consultants": ["charlotte.young@slalom.com", "henry.king@slalom.com"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/capabilities")
def get_capabilities():
    return capabilities


@app.post("/auth/login")
def login(payload: LoginRequest):
    user = practice_lead_store.authenticate(payload.username, payload.password)
    if not user:
        log_audit_event("login_failed", payload.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(32)
    active_sessions[token] = {
        "user": user,
        "expires_at": datetime.now(timezone.utc) + session_lifetime,
    }
    log_audit_event("login_succeeded", user["username"])

    return {
        "token": token,
        "user": user,
    }


@app.post("/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "", 1).strip()
        session = active_sessions.pop(token, None)
        if session:
            log_audit_event("logout", session["user"]["username"])

    return {"message": "Logged out"}


@app.get("/auth/me")
def get_authenticated_user(authorization: str | None = Header(default=None)):
    user = get_current_user(authorization)
    return {"user": user}


@app.post("/capabilities/{capability_name}/register")
def register_for_capability(
    capability_name: str,
    email: str,
    authorization: str | None = Header(default=None),
):
    """Register a consultant for a capability"""
    user = require_practice_lead(authorization)

    # Validate capability exists
    if capability_name not in capabilities:
        raise HTTPException(status_code=404, detail="Capability not found")

    require_practice_area(user, capability_name)

    # Get the specific capability
    capability = capabilities[capability_name]

    # Validate consultant is not already registered
    if email in capability["consultants"]:
        raise HTTPException(
            status_code=400,
            detail="Consultant is already registered for this capability"
        )

    # Add consultant
    capability["consultants"].append(email)
    log_audit_event("consultant_registered", user["username"], capability_name, email)
    return {"message": f"Registered {email} for {capability_name}"}


@app.delete("/capabilities/{capability_name}/unregister")
def unregister_from_capability(
    capability_name: str,
    email: str,
    authorization: str | None = Header(default=None),
):
    """Unregister a consultant from a capability"""
    user = require_practice_lead(authorization)

    # Validate capability exists
    if capability_name not in capabilities:
        raise HTTPException(status_code=404, detail="Capability not found")

    require_practice_area(user, capability_name)

    # Get the specific capability
    capability = capabilities[capability_name]

    # Validate consultant is registered
    if email not in capability["consultants"]:
        raise HTTPException(
            status_code=400,
            detail="Consultant is not registered for this capability"
        )

    # Remove consultant
    capability["consultants"].remove(email)
    log_audit_event("consultant_unregistered", user["username"], capability_name, email)
    return {"message": f"Unregistered {email} from {capability_name}"}

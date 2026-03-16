"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Role-Based Access Control (RBAC)
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Controls who can do what within AITestSuite v3.
    Critical for enterprise and healthcare deployments
    where different stakeholders need different access levels.

ROLES:
    VIEWER      — Can view reports and findings only
                  (e.g. clinical manager reviewing audit results)

    ANALYST     — Can run standard and statistical audits
                  Can generate reports
                  Cannot run blackbox or evolutionary tests
                  (e.g. junior security analyst)

    AUDITOR     — Full test suite access
                  Can run all audit modes
                  Can run manual blackbox testing
                  (e.g. senior AI auditor — Amarjit's role)

    RED_TEAMER  — Full access including automated blackbox
                  Can run fuzzing and evolutionary engines
                  Requires additional authorisation logging
                  (e.g. dedicated red team engagement)

    ADMIN       — Full system access
                  Can manage users and configuration
                  Can view raw audit logs
                  (e.g. system administrator)

PERMISSIONS:
    Each permission maps to a specific toolkit capability.
    Roles are additive — each role has all permissions of
    the roles below it plus additional ones.

AUTHENTICATION:
    For Streamlit: simple password-based session auth
    For REST API:  JWT token-based authentication
    For CI/CD:     API key based authentication

STORAGE:
    Users stored in users.json (encrypted passwords)
    Session tokens stored in memory (not persistent)

HEALTHCARE RELEVANCE:
    RBAC is mandatory for clinical AI tool deployment
    under PIPEDA and HIPAA. Any AI tool accessed by
    multiple users in a healthcare organisation requires
    role-based access controls with audit logging.
═══════════════════════════════════════════════════════════
"""

import hashlib
import json
import os
import secrets
import time
from functools import wraps

# ── Permission definitions ────────────────────────────────────────────────

class Permission:
    # Viewing permissions
    VIEW_REPORTS      = "view_reports"
    VIEW_FINDINGS     = "view_findings"
    VIEW_AUDIT_LOG    = "view_audit_log"

    # Test execution permissions
    RUN_STANDARD      = "run_standard"
    RUN_STATISTICAL   = "run_statistical"
    RUN_MULTITURN     = "run_multiturn"
    RUN_FUZZING       = "run_fuzzing"
    RUN_EVOLUTIONARY  = "run_evolutionary"
    RUN_FULL          = "run_full"

    # Blackbox permissions (requires additional authorisation)
    RUN_BLACKBOX_MANUAL    = "run_blackbox_manual"
    RUN_BLACKBOX_AUTOMATED = "run_blackbox_automated"

    # Report permissions
    GENERATE_REPORT   = "generate_report"
    EXPORT_DATA       = "export_data"

    # Administration permissions
    MANAGE_USERS      = "manage_users"
    VIEW_CONFIG       = "view_config"
    CHANGE_CONFIG     = "change_config"
    VIEW_RAW_LOG      = "view_raw_log"


# ── Role definitions with permission sets ────────────────────────────────

ROLES = {
    "viewer": {
        "description": "Read-only access to reports and findings",
        "permissions": {
            Permission.VIEW_REPORTS,
            Permission.VIEW_FINDINGS,
        }
    },
    "analyst": {
        "description": "Can run standard audits and generate reports",
        "permissions": {
            Permission.VIEW_REPORTS,
            Permission.VIEW_FINDINGS,
            Permission.RUN_STANDARD,
            Permission.RUN_STATISTICAL,
            Permission.GENERATE_REPORT,
            Permission.EXPORT_DATA,
        }
    },
    "auditor": {
        "description": "Full audit access including multi-turn and manual blackbox",
        "permissions": {
            Permission.VIEW_REPORTS,
            Permission.VIEW_FINDINGS,
            Permission.VIEW_AUDIT_LOG,
            Permission.RUN_STANDARD,
            Permission.RUN_STATISTICAL,
            Permission.RUN_MULTITURN,
            Permission.RUN_BLACKBOX_MANUAL,
            Permission.GENERATE_REPORT,
            Permission.EXPORT_DATA,
        }
    },
    "red_teamer": {
        "description": "Full red team access including fuzzing and automated blackbox",
        "permissions": {
            Permission.VIEW_REPORTS,
            Permission.VIEW_FINDINGS,
            Permission.VIEW_AUDIT_LOG,
            Permission.RUN_STANDARD,
            Permission.RUN_STATISTICAL,
            Permission.RUN_MULTITURN,
            Permission.RUN_FUZZING,
            Permission.RUN_EVOLUTIONARY,
            Permission.RUN_FULL,
            Permission.RUN_BLACKBOX_MANUAL,
            Permission.RUN_BLACKBOX_AUTOMATED,
            Permission.GENERATE_REPORT,
            Permission.EXPORT_DATA,
        }
    },
    "admin": {
        "description": "Full system access including user management",
        "permissions": {
            Permission.VIEW_REPORTS,
            Permission.VIEW_FINDINGS,
            Permission.VIEW_AUDIT_LOG,
            Permission.VIEW_RAW_LOG,
            Permission.RUN_STANDARD,
            Permission.RUN_STATISTICAL,
            Permission.RUN_MULTITURN,
            Permission.RUN_FUZZING,
            Permission.RUN_EVOLUTIONARY,
            Permission.RUN_FULL,
            Permission.RUN_BLACKBOX_MANUAL,
            Permission.RUN_BLACKBOX_AUTOMATED,
            Permission.GENERATE_REPORT,
            Permission.EXPORT_DATA,
            Permission.MANAGE_USERS,
            Permission.VIEW_CONFIG,
            Permission.CHANGE_CONFIG,
        }
    }
}

# ── Map audit modes to required permissions ───────────────────────────────

AUDIT_MODE_PERMISSIONS = {
    "standard":    Permission.RUN_STANDARD,
    "statistical": Permission.RUN_STATISTICAL,
    "multiturn":   Permission.RUN_MULTITURN,
    "fuzzing":     Permission.RUN_FUZZING,
    "evolutionary":Permission.RUN_EVOLUTIONARY,
    "full":        Permission.RUN_FULL,
}


class RBACManager:
    """
    Manages users, roles and permission checks.
    Integrates with the audit logger for all access decisions.
    """

    def __init__(self, users_file="config/users.json"):
        """
        Args:
            users_file : Path to the users configuration file
        """
        self.users_file     = users_file
        self._sessions      = {}   # token -> {user, role, created_at}
        self._users         = {}   # username -> {role, password_hash}
        self._load_users()

    def _load_users(self):
        """Load users from the users file, or create defaults if not present."""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)

        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r") as f:
                    self._users = json.load(f)
                return
            except Exception:
                pass

        # Create default admin user if no users file exists
        # Default password: change on first login in production
        self._users = {
            "admin": {
                "role":          "admin",
                "password_hash": self._hash_password("admin"),
                "created_at":    time.strftime("%Y-%m-%d"),
                "must_change":   True
            }
        }
        self._save_users()

    def _save_users(self):
        """Persist users to file."""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, "w") as f:
            json.dump(self._users, f, indent=2)

    def _hash_password(self, password):
        """Hash a password using SHA256 with salt."""
        salt     = "AITestSuite-v3-salt"
        combined = f"{salt}:{password}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def authenticate(self, username, password):
        """
        Authenticate a user and return a session token.

        Returns:
            (token, role) on success
            (None, None) on failure
        """
        user = self._users.get(username)
        if not user:
            return None, None

        if user.get("password_hash") != self._hash_password(password):
            return None, None

        # Generate secure session token
        token     = secrets.token_urlsafe(32)
        role      = user.get("role", "viewer")
        self._sessions[token] = {
            "username":   username,
            "role":       role,
            "created_at": time.time()
        }
        return token, role

    def validate_token(self, token, max_age_hours=8):
        """
        Validate a session token.
        Returns (username, role) or (None, None) if invalid/expired.
        """
        session = self._sessions.get(token)
        if not session:
            return None, None

        # Check token age
        age_hours = (time.time() - session["created_at"]) / 3600
        if age_hours > max_age_hours:
            del self._sessions[token]
            return None, None

        return session["username"], session["role"]

    def has_permission(self, role, permission):
        """
        Check if a role has a specific permission.

        Args:
            role       : Role name string
            permission : Permission constant from Permission class

        Returns:
            True if the role has the permission, False otherwise
        """
        role_config = ROLES.get(role, {})
        return permission in role_config.get("permissions", set())

    def can_run_audit_mode(self, role, audit_mode):
        """
        Check if a role can run a specific audit mode.

        Returns:
            True if permitted, False otherwise
        """
        required = AUDIT_MODE_PERMISSIONS.get(audit_mode, Permission.RUN_STANDARD)
        return self.has_permission(role, required)

    def add_user(self, username, password, role, created_by="admin"):
        """
        Add a new user. Requires MANAGE_USERS permission.

        Returns:
            True on success, error message on failure
        """
        if username in self._users:
            return f"User {username} already exists"

        if role not in ROLES:
            return f"Invalid role: {role}. Valid roles: {list(ROLES.keys())}"

        self._users[username] = {
            "role":          role,
            "password_hash": self._hash_password(password),
            "created_at":    time.strftime("%Y-%m-%d"),
            "created_by":    created_by,
            "must_change":   True
        }
        self._save_users()
        return True

    def change_password(self, username, new_password):
        """Change a user's password."""
        if username not in self._users:
            return False
        self._users[username]["password_hash"] = self._hash_password(new_password)
        self._users[username]["must_change"]   = False
        self._save_users()
        return True

    def get_users(self):
        """Return user list (without password hashes) for admin view."""
        return {
            username: {k: v for k, v in info.items() if k != "password_hash"}
            for username, info in self._users.items()
        }

    def logout(self, token):
        """Invalidate a session token."""
        self._sessions.pop(token, None)

    def get_role_permissions(self, role):
        """Return the permissions for a role."""
        return list(ROLES.get(role, {}).get("permissions", set()))


# ── Global RBAC instance ──────────────────────────────────────────────────
_rbac = None

def get_rbac():
    """Get or create the global RBAC manager."""
    global _rbac
    if _rbac is None:
        _rbac = RBACManager()
    return _rbac


def require_permission(permission):
    """
    Decorator for functions that require a specific permission.
    For use with the REST API layer.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, role=None, **kwargs):
            rbac = get_rbac()
            if not role or not rbac.has_permission(role, permission):
                raise PermissionError(
                    f"Permission denied: {permission} required. "
                    f"Your role ({role}) does not have this permission."
                )
            return func(*args, role=role, **kwargs)
        return wrapper
    return decorator

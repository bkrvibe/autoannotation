# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.tenant import Tenant  # noqa
from app.models.user import User  # noqa
from app.models.user_tenant import UserTenant  # noqa
from app.models.job import Job  # noqa
from app.models.invite import Invite  # noqa
from app.models.session import Session  # noqa
from app.models.magic_link import MagicLink  # noqa
from app.models.password_reset import PasswordResetToken  # noqa
from app.models.audit_log import AuditLog  # noqa

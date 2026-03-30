from accounts.models import AccountAuditEvent


class AccountAuditService:
    @staticmethod
    def log(*, account, action: str, actor=None, metadata: dict | None = None):
        return AccountAuditEvent.objects.create(
            account=account,
            actor=actor,
            action=action,
            metadata=metadata or {},
        )


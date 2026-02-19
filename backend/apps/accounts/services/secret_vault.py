import base64
import hashlib
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError

from accounts.models import BrokerageSecret


class BrokerageSecretVault:
    @staticmethod
    def _fernet():
        try:
            from cryptography.fernet import Fernet  # type: ignore
        except Exception as exc:
            raise ValidationError("cryptography package is required for secure token vault.") from exc

        key_material = (getattr(settings, "BROKERAGE_SECRET_KEY", "") or "").strip()
        if not key_material:
            raise ValidationError("BROKERAGE_SECRET_KEY is not configured.")
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material.encode("utf-8")).digest())
        return Fernet(key)

    @staticmethod
    def store(*, provider: str, plaintext: str) -> str:
        if not plaintext:
            raise ValidationError("Secret plaintext is required.")
        f = BrokerageSecretVault._fernet()
        ciphertext = f.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        reference = f"vault:{provider}:{uuid.uuid4().hex}"
        BrokerageSecret.objects.create(
            reference=reference,
            provider=provider,
            secret_ciphertext=ciphertext,
            is_active=True,
        )
        return reference

    @staticmethod
    def retrieve(*, reference: str) -> str:
        secret = BrokerageSecret.objects.filter(reference=reference, is_active=True).first()
        if not secret:
            raise ValidationError("Token reference not found or inactive.")
        f = BrokerageSecretVault._fernet()
        try:
            plaintext = f.decrypt(secret.secret_ciphertext.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            raise ValidationError("Failed to decrypt token secret.") from exc
        return plaintext

    @staticmethod
    def revoke(*, reference: str):
        BrokerageSecret.objects.filter(reference=reference, is_active=True).update(is_active=False)


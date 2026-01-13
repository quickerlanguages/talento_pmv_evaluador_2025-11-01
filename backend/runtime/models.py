# runtime/models.py
from django.db import models

class TltRespuesta(models.Model):
    sesion_id = models.IntegerField()
    ccp_code = models.CharField(max_length=16)
    ejer_code = models.CharField(max_length=32, blank=True, null=True)
    correcta = models.BooleanField()
    tr_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        db_table = "tlt_respuesta"
        indexes = [
            models.Index(
                fields=["sesion_id", "created_at"],
                name="idx_tlt_respuesta_sesion_fecha",
            ),
        ]

from django.db import models


class SubmodalityGovernanceCache(models.Model):
    """OPS-cache of submodality governance synced from SSOT.

    This table is intentionally denormalized and small. SSOT remains the source of truth.
    """

    class EstadoNormativo(models.TextChoices):
        ACTIVE = "active", "active"
        LATENT = "latent", "latent"
        EXCLUDED = "excluded", "excluded"

    class RiskClass(models.TextChoices):
        LOW = "low", "low"
        MEDIUM = "medium", "medium"
        HIGH = "high", "high"

    submod_code = models.TextField(unique=True)
    estado_normativo = models.TextField(choices=EstadoNormativo.choices)
    risk_class = models.TextField(null=True, blank=True, choices=RiskClass.choices)
    introduced_in_version = models.TextField()
    rules_ref = models.TextField(null=True, blank=True)

    # Metadata about the sync operation (OPS only)
    source_normative_version = models.TextField()
    synced_at_utc = models.DateTimeField()

    class Meta:
        db_table = "submodality_governance_cache"

    def __str__(self) -> str:
        return f"{self.submod_code}={self.estado_normativo}"
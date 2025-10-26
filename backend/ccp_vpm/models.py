from django.db import models

class VpmSubmodality(models.TextChoices):
    VIS_S = "VIS_S", "Visual Simbólica"
    VIS_I = "VIS_I", "Visual Icónica"

class Session(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=64, blank=True, null=True)
    vpm_mode = models.CharField(max_length=16, choices=VpmSubmodality.choices)
    meta = models.JSONField(default=dict, blank=True)

class Item(models.Model):
    submodality = models.CharField(max_length=16, choices=VpmSubmodality.choices)
    difficulty_level = models.PositiveSmallIntegerField(default=1)
    stimulus = models.JSONField()
    options = models.JSONField()
    correct_index = models.PositiveSmallIntegerField()
    params = models.JSONField(default=dict, blank=True)

class Trial(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="trials")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    started_ms = models.IntegerField()
    responded_ms = models.IntegerField()
    response_time_ms = models.IntegerField()
    chosen_index = models.IntegerField()
    is_correct = models.BooleanField()
    client_meta = models.JSONField(default=dict, blank=True)


from django.db import models

class RefCcp(models.Model):
    id_ccp = models.AutoField(primary_key=True)
    codigo = models.TextField(unique=True)
    nombre = models.TextField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'ref_ccp'

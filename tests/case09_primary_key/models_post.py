from django.db import models
import datetime
import deseb

class rA(models.Model):
    "base with min flags"
    c001 = models.AutoField(primary_key=True)
    class Meta:
        aka = 'A'

class rB(models.Model):
    "base with max flags"
    r001 = models.AutoField(primary_key=True, aka='c001')
    class Meta:
        aka = 'B'

class rC(models.Model):
    "all with akas"

    class Meta:
        aka = 'C'

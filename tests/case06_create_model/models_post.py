from django.db import models
import deseb
if deseb.version == '0.96':
    from django.db.models import GenericForeignKey, GenericRelation #@UnresolvedImport
else:
    from django.contrib.contenttypes.generic import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

class Empty(models.Model):
    pass

class Employee(models.Model):
    employee_code = models.CharField(max_length=10, primary_key=True,
            db_column = 'code')
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    class Meta:
        ordering = ('last_name', 'first_name')

    def __unicode__(self):
        return u"%s %s" % (self.first_name, self.last_name)

class Business(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    employees = models.ManyToManyField(Employee)
    class Meta:
        verbose_name_plural = 'businesses'

    def __unicode__(self):
        return self.name

class Lol(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    zzz = GenericForeignKey()

class Fun(models.Model):
    xxx = GenericRelation(Lol)

class TipTop(models.Model):
    yyy = models.OneToOneField(Fun, null=True)

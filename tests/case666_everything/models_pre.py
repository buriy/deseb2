from django.db import models
import datetime
import deseb
 
class A(models.Model):
    "base with min flags"
    c001 = models.AutoField(primary_key=True)
    c002 = models.BooleanField()
    c003 = models.CharField(max_length='256')
    c004 = models.CommaSeparatedIntegerField(max_length='256')
    c005 = models.DateField()
    c006 = models.DateTimeField()
    if deseb.version == 'trunk':
        c007 = models.DecimalField(decimal_places=5, max_digits=10, default='1.2')
    c008 = models.EmailField()
    c010 = models.FileField(upload_to='/tmp')
    c011 = models.FilePathField()
    if deseb.version == 'trunk':
        c012 = models.FloatField()
    else:
        c012 = models.FloatField(decimal_places=5, max_digits=10)
    c013 = models.IPAddressField()
    c014 = models.ImageField(upload_to='/tmp')
    c015 = models.IntegerField()
    c016 = models.NullBooleanField()
#    c017 = models.OrderingField(max_length='256')
    c018 = models.PhoneNumberField()
    c019 = models.PositiveIntegerField()
    c020 = models.PositiveSmallIntegerField()
    c021 = models.SlugField()
    c022 = models.SmallIntegerField()
    c023 = models.TextField()
    c024 = models.TimeField()
    c025 = models.URLField()
    c026 = models.USStateField()
    c027 = models.XMLField()

class B(models.Model):
    "base with max flags"
    c001 = models.AutoField(primary_key=True)
    c002 = models.BooleanField(default=False)
    c003 = models.CharField(max_length='256', default='x')
    c004 = models.CommaSeparatedIntegerField(max_length='256', default='1')
    c005 = models.DateField(default=datetime.date(2007,1,1))
    c006 = models.DateTimeField(default=datetime.datetime(2007,1,1))
    if deseb.version == 'trunk':
        c007 = models.DecimalField(decimal_places=5, max_digits=10, default=2)
    c008 = models.EmailField(default='x')
    c010 = models.FileField(upload_to='/tmp')
    c011 = models.FilePathField(default='x')
    if deseb.version == 'trunk':
        c012 = models.FloatField(aka='xxx')
    else:
        c012 = models.FloatField(aka='xxx', decimal_places=5, max_digits=10)
    c013 = models.IPAddressField()
    c014 = models.ImageField(upload_to='/tmp')
    c015 = models.IntegerField(default=2)
    c016 = models.NullBooleanField(default=True)
#    c017 = models.OrderingField(max_length='256')
    c018 = models.PhoneNumberField(default='555-867-5309')
    c019 = models.PositiveIntegerField(default=7)
    c020 = models.PositiveSmallIntegerField(default=6)
    c021 = models.SlugField(default='x')
    c022 = models.SmallIntegerField(default=-2)
    c023 = models.TextField(default='x')
    c024 = models.TimeField(default=datetime.time(12,12,12))
    c025 = models.URLField(default='x')
    c026 = models.USStateField(default='TX')
    c027 = models.XMLField(default='x')

class C(models.Model):
    "all with akas"
    id = models.AutoField(primary_key=True)
    c002 = models.BooleanField(aka='xxx')
    c003 = models.CharField(max_length='256', aka='xxx')
    c004 = models.CommaSeparatedIntegerField(max_length='256', aka='xxx')
    c005 = models.DateField(aka='xxx')
    c006 = models.DateTimeField(aka='xxx')
    if deseb.version == 'trunk':
        c007 = models.DecimalField(decimal_places=5, max_digits=10, aka='xxx', default=3)
    c008 = models.EmailField(aka='xxx')
    c010 = models.FileField(upload_to='/tmp', aka='xxx')
    c011 = models.FilePathField(aka='xxx')
    if deseb.version == 'trunk':
        c012 = models.FloatField(aka='xxx')
    else:
        c012 = models.FloatField(aka='xxx', decimal_places=5, max_digits=10)
    c013 = models.IPAddressField(aka='xxx')
    c014 = models.ImageField(upload_to='/tmp', aka='xxx')
    c015 = models.IntegerField(aka='xxx')
    c016 = models.NullBooleanField(aka='xxx')
#    c017 = models.OrderingField(max_length='256')
    c018 = models.PhoneNumberField(aka='xxx')
    c019 = models.PositiveIntegerField(aka='xxx')
    c020 = models.PositiveSmallIntegerField(aka='xxx')
    c021 = models.SlugField(aka='xxx')
    c022 = models.SmallIntegerField(aka='xxx')
    c023 = models.TextField(aka='xxx')
    c024 = models.TimeField(aka='xxx')
    c025 = models.URLField(aka='xxx')
    c026 = models.USStateField(aka='xxx')
    c027 = models.XMLField(aka='xxx')

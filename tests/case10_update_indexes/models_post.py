from django.db import models

class Poll(models.Model):
    question = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date published')
    author = models.CharField(max_length=200)
    def __str__(self):
        return self.question
    
class Choice(models.Model):
    "the original name for this model was 'Choice'"
    poll = models.ForeignKey(Poll)
    option = models.CharField(max_length=400, aka='choice') # make sure aka still works
    votes = models.IntegerField()
    votes2 = models.IntegerField(default='-5') # make sure column adds still work
    def __str__(self):
        return self.choice

class Foo(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, db_index=True)
    gender2 = models.CharField(max_length=1, null=True, unique=True)
        
class Poll2(models.Model):
    question = models.CharField(max_length=100, db_index=True)
    pub_date = models.DateTimeField('date published', db_index=True)
    author = models.CharField(max_length=200, db_index=True)
    def __str__(self):
        return self.question
    
class Choice2(models.Model):
    "the original name for this model was 'Choice'"
    poll = models.ForeignKey(Poll, db_index=True)
    option = models.CharField(max_length=400, aka='choice', db_index=True) # make sure aka still works
    votes = models.IntegerField(db_index=True)
    votes2 = models.IntegerField(default='-5', db_index=True) # make sure column adds still work
    def __str__(self):
        return self.choice

class Foo2(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, db_index=True)
    gender2 = models.CharField(max_length=1, null=True, unique=True, db_index=True)
        

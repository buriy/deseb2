from django.db import models

class Poll(models.Model):
    question = models.CharField(max_length=200, db_index=True)
    pub_date = models.DateTimeField('date published', db_index=True)
    author = models.CharField(max_length=200, db_index=True)
    def __str__(self):
        return self.question
    
class Choice(models.Model):
    "the original name for this model was 'Choice'"
    poll = models.ForeignKey(Poll, db_index=True)
    choice = models.CharField(max_length=200, db_index=True, aka='choice') # make sure aka still works
    votes = models.IntegerField(db_index=True)
    def __str__(self):
        return self.choice

class Foo(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, db_index=True, choices=GENDER_CHOICES)

class Poll2(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    author = models.CharField(max_length=200)
    def __str__(self):
        return self.question
    
class Choice2(models.Model):
    "the original name for this model was 'Choice'"
    poll = models.ForeignKey(Poll)
    choice = models.CharField(max_length=200, aka='choice') # make sure aka still works
    votes = models.IntegerField()
    def __str__(self):
        return self.choice

class Foo2(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

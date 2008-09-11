from django.db import models
import deseb

class Poll(models.Model):
    question = models.CharField(max_length=200, aka='')
    pub_date = models.DateTimeField('date published', aka='')
    author = models.CharField(max_length=200)
    def __str__(self):
        return self.question
    
class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    choice = models.CharField(max_length=200)
    votes = models.IntegerField()
    def __str__(self):
        return self.choice
    

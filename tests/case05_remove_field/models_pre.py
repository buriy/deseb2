from django.db import models
import deseb

class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    author = models.CharField(max_length=200, default='')
    def __str__(self):
        return self.question
    
class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    choice = models.CharField(max_length=200, aka='option')
    votes = models.IntegerField(aka='number_of_votes')
    def __str__(self):
        return self.choice

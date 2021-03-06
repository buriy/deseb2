from django.db import models
import deseb

class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    author = models.CharField(max_length=200)
    def __str__(self):
        return self.question
    
class Choice(models.Model):
    "the original name for this model was 'Choice'"
    poll = models.ForeignKey(Poll)
    choice = models.CharField(max_length=200)
    number_of_votes = models.IntegerField(aka='number_of_votes', default='0') # show that field name changes work too
    def __str__(self):
        return self.choice
    class Meta:
        aka = ('Choice', 'OtherBadName', 'Option')

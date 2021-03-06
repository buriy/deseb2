from django.db import models
import deseb

class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    author = models.CharField(max_length=200)
    def __str__(self):
        return self.question
    
    # new fields
    pub_date2 = models.DateTimeField('date published', null=True)

class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    choice = models.CharField(max_length=200)
    votes = models.IntegerField()
    def __str__(self):
        return self.choice
    
    # new fields
    votes2 = models.IntegerField(default=0)
    hasSomething = models.BooleanField(default=False)
    creatorIp = models.IPAddressField(null=True)
    votes3 = models.IntegerField(default=5)
    content = models.TextField(default="")

#print Poll.__class__()
#print Choice.__class__()
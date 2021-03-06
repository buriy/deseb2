from django.db import models
import deseb

class Channel(models.Model):
    url = models.URLField(verify_exists = False)
    ADVERT_LIST = (('1','1'),('2','2'))
    source = models.CharField(max_length=50, choices = ADVERT_LIST, blank=True)
    last_updated = models.DateTimeField(auto_now_add=True)
    visits = models.IntegerField(default=0)

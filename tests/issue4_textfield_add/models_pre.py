from django.db import models
import deseb

class Topic(models.Model):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField()
    feature = models.IntegerField(default=0)
    hidden = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    CATEGORY_CHOICES = (('Blog', 'Blog'),
                        ('Food', 'Food'),
                        ('Toys', 'Toys'),
                        )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    create_date = models.DateField('date added', auto_now_add=True)
    updated_date = models.DateField('date updated', auto_now=True)

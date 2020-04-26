from django.contrib.postgres.fields import ArrayField
from django.db import models

from .apps import IsfahanConfig
from .validators import phone_validator

db_name_prefix = f'{IsfahanConfig.name.lower()}_'


class Category(models.Model):
    name = models.TextField()
    name_english = models.TextField()

    class Meta:
        db_table = db_name_prefix + 'categories'
        unique_together = ['name', 'name_english']
        verbose_name_plural = 'categories'
        ordering = ['name_english']


class Location(models.Model):
    name = models.TextField()
    name_english = models.TextField()
    href = models.URLField(null=True)

    class Meta:
        db_table = db_name_prefix + 'locations'
        unique_together = ['name', 'name_english']
        ordering = ['name']


class Person(models.Model):
    number = models.TextField(validators=[phone_validator])
    publisher_type = models.TextField()
    locations = models.ManyToManyField(
        Location,
        through='Article',
        related_name='persons',
    )

    class Meta:
        db_table = db_name_prefix + 'persons'
        unique_together = ['number', 'publisher_type']


class Article(models.Model):
    title = models.TextField()
    date_published = models.DateField()
    time_published = models.TimeField(null=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    area_size = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    price = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    description = models.TextField()
    uri = models.URLField(null=True)
    datetime_crawled = models.DateTimeField(null=True)
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = db_name_prefix + 'articles'
        default_related_name = 'articles'
        get_latest_by = ['date_published', 'time_published']
        ordering = ['-date_published', '-time_published']

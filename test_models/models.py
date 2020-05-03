from django.db import models


class TestModel(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)

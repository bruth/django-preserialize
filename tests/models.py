from django.db import models
from django.contrib.auth.models import User


class Tag(models.Model):
    name = models.CharField(max_length=20)


class Library(models.Model):
    name = models.CharField(max_length=30)
    url = models.URLField()
    language = models.CharField(max_length=20)
    tags = models.ManyToManyField(Tag, related_name='libraries')


class Hacker(models.Model):
    user = models.OneToOneField(User, related_name='profile', primary_key=True)
    website = models.URLField()
    libraries = models.ManyToManyField(Library, related_name='hackers')

    def signature(self):
        return '{0}  <{1}>  {2}'.format(self.user.get_full_name(),
                self.user.email, self.website)

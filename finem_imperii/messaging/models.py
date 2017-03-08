from django.db import models


class CharacterNotification(models.Model):
    class Meta:
        ordering = ['creation_time']

    TRAVEL = 'travel'
    CATEGORY_CHOICES = (
        (TRAVEL, TRAVEL),
    )

    character = models.ForeignKey('world.Character')
    content = models.TextField()
    category = models.CharField(max_length=15)
    creation_time = models.DateTimeField(auto_now_add=True)
    creation_turn = models.IntegerField()
    read = models.BooleanField(default=False)

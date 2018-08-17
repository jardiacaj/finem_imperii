from django.db import models
from django.urls import reverse
from django.utils.html import format_html


class PolicyDocument(models.Model):
    organization = models.ForeignKey('Organization', models.CASCADE)
    parent = models.ForeignKey(
        'PolicyDocument', models.SET_NULL, related_name='children', null=True,
        blank=True)
    public = models.BooleanField(default=False)
    title = models.TextField(max_length=100)
    body = models.TextField()
    last_modified_turn = models.IntegerField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'organization:document', kwargs={'document_id': self.id})

    def get_html_link(self):
        return format_html('<a href="{url}">{name}</a>',
                           url=self.get_absolute_url(),
                           name=self.title,
                           )

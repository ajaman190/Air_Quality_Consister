from django.db import models
from django.contrib.auth.models import User as AuthUser

class ProcessedFile(models.Model):
    STATUS_CHOICES = [
        ('Read-to-Upload', 'Read-to-Upload'),
        ('Read-to-Process', 'Read-to-Process'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Corrupted', 'Corrupted'),
    ]

    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    unprocessed_file_url = models.URLField()
    processed_file_url = models.URLField(null=True, blank=True)
    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Processing')

    def __str__(self):
        return f"{self.user.username}'s File - {self.status}"

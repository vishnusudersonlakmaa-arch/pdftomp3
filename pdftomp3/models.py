from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta


class Profile(models.Model):
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_pic  = models.ImageField(upload_to="profile_pics", blank=True)
    name         = models.CharField(max_length=225)
    username     = models.CharField(max_length=225)
    passwords    = models.CharField(max_length=225)
    mobile_phone = models.CharField(max_length=225, default="xxxx")
    email        = models.EmailField(max_length=225, default="xxxx")
    POSITION     = models.CharField(max_length=100, default="xxxx")

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return self.user.username


class PDFFile(models.Model):
    pdf_file = models.FileField(upload_to="pdfs")
    title    = models.CharField(max_length=255)
    date     = models.DateTimeField(auto_now_add=True, db_index=True)
    user     = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="pdfs")

    class Meta:
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["title"]),       # speeds up icontains search
        ]

    def __str__(self):
        return self.title


class MP3File(models.Model):
    mp3_file = models.FileField(upload_to="mp3s")
    title    = models.CharField(max_length=255)
    date     = models.DateTimeField(auto_now_add=True, db_index=True)
    user     = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="mp3s")

    class Meta:
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["title"]),       # speeds up icontains search
        ]

    def __str__(self):
        return self.title


class UserActivity(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time   = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "end_time"]),
        ]

    def duration(self) -> timedelta:
        """Returns the session duration, or zero for still-open sessions."""
        if self.end_time and self.end_time > self.start_time:
            return self.end_time - self.start_time
        return timedelta(0)

    def __str__(self):
        return f"{self.user.username} — {self.start_time:%Y-%m-%d %H:%M}"
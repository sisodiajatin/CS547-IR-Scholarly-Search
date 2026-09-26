from django.conf import settings
from django.db import models


MAJORS = [("cs", "Computer science"), ("ds", "Data science"),
          ("ms", "Mathematics"), ("ece", "Electrical & computer engineering")]


class umTester(models.Model):
    """Legacy account records; credentials are cleared by the migration."""
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=64)
    major = models.CharField(max_length=64)


class pdTester(models.Model):
    """Preserved legacy paper table."""
    title = models.TextField()
    summary = models.TextField()
    authors = models.TextField()
    published = models.DateTimeField()
    url = models.TextField()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    major = models.CharField(max_length=3, choices=MAJORS)


class Paper(models.Model):
    title = models.TextField()
    summary = models.TextField()
    authors = models.TextField()
    published = models.DateField(db_index=True, null=True, blank=True)
    url = models.URLField(max_length=500)

    class Meta:
        ordering = ["-published", "id"]
        constraints = [models.UniqueConstraint(fields=["url"], name="unique_paper_url")]

    def __str__(self):
        return self.title


class PaperRedirect(models.Model):
    """Keep links to consolidated duplicate records working."""
    old_id = models.BigIntegerField(primary_key=True)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)


class SavedPaper(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["user", "paper"], name="unique_saved_paper")]

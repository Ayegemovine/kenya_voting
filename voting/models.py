from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class VoterProfile(models.Model):
    """
    Extends the standard User with election-specific data and system roles.
    Optimized with indexing for large-scale datasets (1M+ records).
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('voter', 'Standard Voter'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # db_index=True ensures fast filtering by county on the dashboard
    county = models.CharField(max_length=100, db_index=True)
    
    # unique=True already creates an index, but we keep it explicit
    national_id = models.CharField(max_length=20, unique=True)
    
    # Indexed to speed up "Who hasn't voted" queries
    has_voted = models.BooleanField(default=False, db_index=True)
    
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='voter',
        help_text="Determines dashboard access level.",
        db_index=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} ({self.county})"

    class Meta:
        # Combined index for common dashboard queries
        indexes = [
            models.Index(fields=['county', 'has_voted']),
        ]


class Question(models.Model):
    """
    Represents a poll category with an expiration timeline.
    """
    text = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Optional context for the voter")
    order = models.IntegerField(default=1, help_text="Determines the order on the ballot")
    is_text_answer = models.BooleanField(default=False, help_text="Check if this is an open-ended question")
    
    created_at = models.DateTimeField(default=timezone.now) 
    deadline = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="The date and time when this poll closes and expires.",
        db_index=True # Added index for "Active Polls" checks
    )

    def __str__(self):
        return self.text

    @property
    def is_active(self):
        if self.deadline:
            return timezone.now() < self.deadline
        return True 

    class Meta:
        ordering = ['order', '-created_at']


class Choice(models.Model):
    """
    Represents a candidate or option within a specific Question.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    option_text = models.CharField(max_length=200)
    party = models.CharField(max_length=100, blank=True)
    votes = models.IntegerField(default=0, db_index=True) # Added index for results sorting

    def __str__(self):
        return f"{self.option_text} - {self.question.text}"


class Vote(models.Model):
    """
    Audit log of participation (Voter side). 
    """
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(null=True, blank=True)
    voted_at = models.DateTimeField(auto_now_add=True, db_index=True) # Added index for timeline analytics

    def __str__(self):
        return f"{self.voter.username} cast a ballot for: {self.question.text[:40]}"


class AuditLog(models.Model):
    """
    Tracks administrative actions for security and transparency.
    """
    admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'is_staff': True}
    )
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True) # Added index for recent logs

    def __str__(self):
        return f"{self.admin} - {self.action} @ {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
from django.db import models
import uuid
from django.utils import timezone


class EstimationSession(models.Model):
    """Main estimation session that users join"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    current_task = models.ForeignKey('Task', null=True, blank=True, on_delete=models.SET_NULL, related_name='active_in_sessions')
    voting_timer_seconds = models.IntegerField(default=60)  # Default 60 seconds for voting
    voting_started_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Participant(models.Model):
    """Users participating in an estimation session"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('participant', 'Participant'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(EstimationSession, on_delete=models.CASCADE, related_name='participants')
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_online = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.session.name})"

    class Meta:
        ordering = ['joined_at']
        unique_together = ['session', 'name']


class UserStory(models.Model):
    """User stories to be estimated"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(EstimationSession, on_delete=models.CASCADE, related_name='user_stories')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def total_estimate(self):
        """Sum of all task estimates"""
        return sum(task.final_estimate or 0 for task in self.tasks.all())

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name_plural = 'User stories'


class Task(models.Model):
    """Individual tasks under user stories to be estimated"""
    ESTIMATE_CHOICES = [
        (0, '0'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (5, '5'),
        (8, '8'),
        (13, '13'),
        (21, '21'),
        (34, '34'),
        (55, '55'),
        (89, '89'),
        (999, '?'),  # Unknown
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_story = models.ForeignKey(UserStory, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    final_estimate = models.IntegerField(null=True, blank=True, choices=ESTIMATE_CHOICES)
    is_voting = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def all_voted(self):
        """Check if all participants have voted"""
        total_participants = self.user_story.session.participants.filter(is_online=True).count()
        total_votes = self.votes.count()
        return total_participants > 0 and total_votes >= total_participants

    class Meta:
        ordering = ['order', 'created_at']


class Vote(models.Model):
    """Individual vote on a task"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='votes')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='votes')
    estimate = models.IntegerField(choices=Task.ESTIMATE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.participant.name} voted {self.estimate} on {self.task.title}"

    class Meta:
        unique_together = ['task', 'participant']
        ordering = ['created_at']

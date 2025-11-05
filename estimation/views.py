from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import EstimationSession, Participant, UserStory, Task, Vote
import json


def index(request):
    """Home page with option to create or join session"""
    return render(request, 'estimation/index.html')


def create_session(request):
    """Create a new estimation session"""
    if request.method == 'POST':
        name = request.POST.get('session_name')
        admin_name = request.POST.get('admin_name')

        session = EstimationSession.objects.create(name=name)
        participant = Participant.objects.create(
            session=session,
            name=admin_name,
            role='admin'
        )

        # Store participant ID in session
        request.session[f'participant_{session.id}'] = str(participant.id)

        return redirect('session_detail', session_id=session.id)

    return render(request, 'estimation/create_session.html')


def join_session(request, session_id):
    """Join an existing session"""
    session = get_object_or_404(EstimationSession, id=session_id)

    if request.method == 'POST':
        participant_name = request.POST.get('participant_name')

        # Check if participant already exists
        participant, created = Participant.objects.get_or_create(
            session=session,
            name=participant_name,
            defaults={'role': 'participant', 'is_online': True}
        )

        if not created:
            participant.is_online = True
            participant.save()

        # Store participant ID in session
        request.session[f'participant_{session.id}'] = str(participant.id)

        return redirect('session_detail', session_id=session.id)

    return render(request, 'estimation/join_session.html', {'session': session})


def session_detail(request, session_id):
    """Main session view"""
    session = get_object_or_404(EstimationSession, id=session_id)
    participant_id = request.session.get(f'participant_{session.id}')

    if not participant_id:
        return redirect('join_session', session_id=session_id)

    participant = get_object_or_404(Participant, id=participant_id, session=session)
    user_stories = session.user_stories.all().prefetch_related('tasks')

    context = {
        'session': session,
        'participant': participant,
        'user_stories': user_stories,
        'is_admin': participant.role == 'admin',
    }

    return render(request, 'estimation/session_detail.html', context)


@require_http_methods(["POST"])
def add_user_story(request, session_id):
    """Add a new user story"""
    session = get_object_or_404(EstimationSession, id=session_id)
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if participant.role != 'admin':
        return JsonResponse({'error': 'Only admin can add user stories'}, status=403)

    title = request.POST.get('title')
    description = request.POST.get('description', '')

    user_story = UserStory.objects.create(
        session=session,
        title=title,
        description=description,
        order=session.user_stories.count()
    )

    return JsonResponse({
        'id': str(user_story.id),
        'title': user_story.title,
        'description': user_story.description,
    })


@require_http_methods(["POST"])
def add_task(request, user_story_id):
    """Add a new task to a user story"""
    user_story = get_object_or_404(UserStory, id=user_story_id)
    participant_id = request.session.get(f'participant_{user_story.session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=user_story.session)

    if participant.role != 'admin':
        return JsonResponse({'error': 'Only admin can add tasks'}, status=403)

    title = request.POST.get('title')
    description = request.POST.get('description', '')

    task = Task.objects.create(
        user_story=user_story,
        title=title,
        description=description,
        order=user_story.tasks.count()
    )

    return JsonResponse({
        'id': str(task.id),
        'title': task.title,
        'description': task.description,
    })


@require_http_methods(["POST"])
def start_voting(request, task_id):
    """Start voting on a task"""
    task = get_object_or_404(Task, id=task_id)
    session = task.user_story.session
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if participant.role != 'admin':
        return JsonResponse({'error': 'Only admin can start voting'}, status=403)

    # Reset any current voting tasks
    Task.objects.filter(user_story__session=session, is_voting=True).update(is_voting=False)

    # Start voting on this task
    task.is_voting = True
    task.save()

    # Clear previous votes
    task.votes.all().delete()

    # Update session
    session.current_task = task
    session.voting_started_at = timezone.now()
    session.save()

    return JsonResponse({'status': 'voting_started', 'task_id': str(task.id)})


@require_http_methods(["POST"])
def cast_vote(request, task_id):
    """Cast a vote on a task"""
    task = get_object_or_404(Task, id=task_id)
    session = task.user_story.session
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if not task.is_voting:
        return JsonResponse({'error': 'Voting is not active for this task'}, status=400)

    estimate = int(request.POST.get('estimate'))

    # Create or update vote
    vote, created = Vote.objects.update_or_create(
        task=task,
        participant=participant,
        defaults={'estimate': estimate}
    )

    # Check if all participants have voted
    all_voted = task.all_voted

    return JsonResponse({
        'status': 'vote_cast',
        'all_voted': all_voted,
        'vote_count': task.votes.count(),
    })


@require_http_methods(["POST"])
def end_voting(request, task_id):
    """End voting on a task and reveal results"""
    task = get_object_or_404(Task, id=task_id)
    session = task.user_story.session
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if participant.role != 'admin':
        return JsonResponse({'error': 'Only admin can end voting'}, status=403)

    task.is_voting = False
    task.save()

    # Get all votes
    votes = list(task.votes.values('participant__name', 'estimate'))

    # Calculate average (excluding '?' votes)
    numeric_votes = [v['estimate'] for v in votes if v['estimate'] != 999]
    average = sum(numeric_votes) / len(numeric_votes) if numeric_votes else 0

    return JsonResponse({
        'status': 'voting_ended',
        'votes': votes,
        'average': round(average, 1),
    })


@require_http_methods(["POST"])
def set_final_estimate(request, task_id):
    """Set the final estimate for a task"""
    task = get_object_or_404(Task, id=task_id)
    session = task.user_story.session
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if participant.role != 'admin':
        return JsonResponse({'error': 'Only admin can set final estimate'}, status=403)

    estimate = int(request.POST.get('estimate'))
    task.final_estimate = estimate
    task.save()

    return JsonResponse({
        'status': 'estimate_set',
        'estimate': estimate,
        'user_story_total': task.user_story.total_estimate,
    })


def get_session_state(request, session_id):
    """Get current session state for live updates"""
    session = get_object_or_404(EstimationSession, id=session_id)

    participants = list(session.participants.filter(is_online=True).values('id', 'name', 'role'))

    current_task = None
    if session.current_task:
        votes_count = session.current_task.votes.count()
        current_task = {
            'id': str(session.current_task.id),
            'title': session.current_task.title,
            'is_voting': session.current_task.is_voting,
            'votes_count': votes_count,
            'all_voted': session.current_task.all_voted,
        }

    return JsonResponse({
        'participants': participants,
        'current_task': current_task,
        'voting_started_at': session.voting_started_at.isoformat() if session.voting_started_at else None,
    })

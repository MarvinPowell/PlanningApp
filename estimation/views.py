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
def start_voting(request, user_story_id):
    """Start voting on all tasks in a user story"""
    user_story = get_object_or_404(UserStory, id=user_story_id)
    session = user_story.session
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if participant.role != 'admin':
        return JsonResponse({'error': 'Only admin can start voting'}, status=403)

    # Clear previous votes for all tasks without final estimates
    for task in user_story.tasks.filter(final_estimate__isnull=True):
        task.votes.all().delete()

    # Update session to start voting
    session.current_user_story = user_story
    session.is_voting = True
    session.voting_started_at = timezone.now()
    session.save()

    return JsonResponse({'status': 'voting_started', 'user_story_id': str(user_story.id)})


@require_http_methods(["POST"])
def revote_user_story(request, user_story_id):
    """Clear all votes and final estimates for a user story and restart voting"""
    user_story = get_object_or_404(UserStory, id=user_story_id)
    session = user_story.session
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if participant.role != 'admin':
        return JsonResponse({'error': 'Only admin can restart voting'}, status=403)

    # Clear all votes for all tasks in this user story
    for task in user_story.tasks.all():
        task.votes.all().delete()
        # Clear final estimates
        task.final_estimate = None
        task.save()

    # Update session to start voting
    session.current_user_story = user_story
    session.is_voting = True
    session.voting_started_at = timezone.now()
    session.save()

    return JsonResponse({'status': 'revoting_started', 'user_story_id': str(user_story.id)})


@require_http_methods(["POST"])
def cast_vote(request, task_id):
    """Cast a vote on a task"""
    task = get_object_or_404(Task, id=task_id)
    session = task.user_story.session
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if not session.is_voting or session.current_user_story_id != task.user_story_id:
        return JsonResponse({'error': 'Voting is not active for this task'}, status=400)

    estimate = int(request.POST.get('estimate'))

    # Create or update vote
    vote, created = Vote.objects.update_or_create(
        task=task,
        participant=participant,
        defaults={'estimate': estimate}
    )

    # Check if all participants have voted on all tasks in the user story
    user_story = task.user_story
    all_tasks_voted = user_story.all_tasks_voted()

    response_data = {
        'status': 'vote_cast',
        'all_voted': all_tasks_voted,
        'vote_count': task.votes.count(),
    }

    # Auto-end voting if all tasks are voted on
    if all_tasks_voted:
        session.is_voting = False
        session.save()

        # Collect all voting results
        tasks_results = []
        for t in user_story.tasks.filter(final_estimate__isnull=True):
            votes = list(t.votes.values('participant__name', 'estimate'))
            numeric_votes = [v['estimate'] for v in votes if v['estimate'] != 999]
            average = sum(numeric_votes) / len(numeric_votes) if numeric_votes else 0

            tasks_results.append({
                'task_id': str(t.id),
                'task_title': t.title,
                'votes': votes,
                'average': round(average, 1),
            })

        response_data['voting_ended'] = True
        response_data['results'] = tasks_results

    return JsonResponse(response_data)


@require_http_methods(["POST"])
def end_voting(request, session_id):
    """End voting on current user story (admin override)"""
    session = get_object_or_404(EstimationSession, id=session_id)
    participant_id = request.session.get(f'participant_{session.id}')
    participant = get_object_or_404(Participant, id=participant_id, session=session)

    if participant.role != 'admin':
        return JsonResponse({'error': 'Only admin can end voting'}, status=403)

    if not session.is_voting or not session.current_user_story:
        return JsonResponse({'error': 'No active voting session'}, status=400)

    user_story = session.current_user_story
    session.is_voting = False
    session.save()

    # Collect all voting results
    tasks_results = []
    for task in user_story.tasks.filter(final_estimate__isnull=True):
        votes = list(task.votes.values('participant__name', 'estimate'))
        numeric_votes = [v['estimate'] for v in votes if v['estimate'] != 999]
        average = sum(numeric_votes) / len(numeric_votes) if numeric_votes else 0

        tasks_results.append({
            'task_id': str(task.id),
            'task_title': task.title,
            'votes': votes,
            'average': round(average, 1),
        })

    return JsonResponse({
        'status': 'voting_ended',
        'results': tasks_results,
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
    participant_id = request.session.get(f'participant_{session.id}')

    participants = list(session.participants.filter(is_online=True).values('id', 'name', 'role'))

    current_user_story = None
    voting_tasks = []
    if session.is_voting and session.current_user_story:
        user_story = session.current_user_story

        # Get all tasks without final estimates
        tasks = user_story.tasks.filter(final_estimate__isnull=True)

        for task in tasks:
            votes_count = task.votes.count()
            user_has_voted = False

            # Check if current user has voted on this task
            if participant_id:
                user_has_voted = task.votes.filter(participant_id=participant_id).exists()

            voting_tasks.append({
                'id': str(task.id),
                'title': task.title,
                'description': task.description,
                'votes_count': votes_count,
                'all_voted': task.all_voted,
                'user_has_voted': user_has_voted,
            })

        current_user_story = {
            'id': str(user_story.id),
            'title': user_story.title,
            'description': user_story.description,
            'all_voted': user_story.all_tasks_voted(),
        }

    return JsonResponse({
        'participants': participants,
        'is_voting': session.is_voting,
        'current_user_story': current_user_story,
        'voting_tasks': voting_tasks,
        'voting_started_at': session.voting_started_at.isoformat() if session.voting_started_at else None,
    })

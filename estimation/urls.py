from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_session, name='create_session'),
    path('session/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('session/<uuid:session_id>/join/', views.join_session, name='join_session'),
    path('session/<uuid:session_id>/add-user-story/', views.add_user_story, name='add_user_story'),
    path('user-story/<uuid:user_story_id>/add-task/', views.add_task, name='add_task'),
    path('user-story/<uuid:user_story_id>/start-voting/', views.start_voting, name='start_voting'),
    path('user-story/<uuid:user_story_id>/revote/', views.revote_user_story, name='revote_user_story'),
    path('task/<uuid:task_id>/cast-vote/', views.cast_vote, name='cast_vote'),
    path('session/<uuid:session_id>/end-voting/', views.end_voting, name='end_voting'),
    path('task/<uuid:task_id>/set-estimate/', views.set_final_estimate, name='set_final_estimate'),
    path('session/<uuid:session_id>/state/', views.get_session_state, name='get_session_state'),
]

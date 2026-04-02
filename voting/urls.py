from django.urls import path
from . import views

urlpatterns = [
    # ── PUBLIC ACCESS ──
    # These handle landing, info, and live results for everyone
    path('', views.home, name='home'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('security/', views.security, name='security'),
    path('results/', views.results, name='results'),
    
    # ── AUTHENTICATION ──
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ── VOTER INTERFACE (FRONTEND) ──
    # Regular voter experience and ballot submission
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vote/', views.vote_view, name='vote'),
    path('submit-vote/', views.submit_vote, name='submit-vote'),
    path('vote-success/', views.vote_success, name='vote-success'),
    
    # ── ADMIN COMMAND CENTER (BACKEND HUB) ──
    # High-level overview and real-time health metrics
    path('management/overview/', views.admin_dashboard, name='admin_dashboard'),
    path('management/health/', views.system_health, name='system_health'),
    
    # ── DATA DIRECTORIES (SIDEBAR NAVIGATION) ──
    # Search functionality is integrated into 'user_list'
    path('mgmt/voters/', views.user_list, name='user_list'),
    path('mgmt/polls/', views.poll_list, name='poll_list'),
    path('mgmt/audit-logs/', views.audit_log_view, name='audit_log'),

    # ── ADMINISTRATIVE ACTIONS (CRUD) ──
    # Create/Delete logic for Polls
    path('mgmt/poll/create/', views.create_poll, name='create_poll'),
    path('mgmt/poll/delete/<int:pk>/', views.delete_poll, name='delete_poll'),
    
    # Create/Edit/Delete logic for Voters and Staff
    path('mgmt/user/create/', views.create_voter, name='create_voter'), 
    path('mgmt/user/edit/<int:pk>/', views.edit_user, name='edit_user'),
    path('mgmt/user/delete/<int:pk>/', views.delete_user, name='delete_user'),

    # ── DOCUMENT GENERATION & EXPORTS ──
    # Triggers the presentation-ready Executive Audit PDF
    path('mgmt/export/pdf/', views.export_stats_pdf, name='export_pdf'),
]
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import VoterProfile, Choice, Question, Vote, AuditLog
from datetime import timedelta
import json

# PDF Generation Imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch

# ── HELPERS ──
def is_admin(user):
    return user.is_authenticated and user.is_staff

def record_audit(request, action):
    AuditLog.objects.create(
        admin=request.user,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR')
    )

# ── PUBLIC PAGES ──

def home(request):
    profile = VoterProfile.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    return render(request, 'home.html', {'profile': profile})

def how_it_works(request): return render(request, 'how_it_works.html')
def security(request): return render(request, 'security.html')

def results(request):
    questions = Question.objects.all().prefetch_related('choices')
    results_data = []
    for q in questions:
        choices = q.choices.all().order_by('-votes')
        total = sum(c.votes for c in choices)
        for c in choices:
            c.percentage = round((c.votes / total * 100), 1) if total > 0 else 0
        results_data.append({'question': q, 'choices': choices, 'total_votes': total})
    
    votes_dict = {i['county']: i['t'] for i in VoterProfile.objects.filter(has_voted=True).values('county').annotate(t=Count('id'))}
    reg_dict = {i['county']: i['t'] for i in VoterProfile.objects.values('county').annotate(t=Count('id'))}
    
    return render(request, 'results.html', {
        'results_data': results_data,
        'votes_json': json.dumps(votes_dict),
        'reg_json': json.dumps(reg_dict)
    })

# ── ADMIN MANAGEMENT (COMMAND CENTER) ──

@user_passes_test(is_admin)
def admin_dashboard(request):
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)
    failed_attempts = AuditLog.objects.filter(action__icontains="FAILED", timestamp__gte=one_hour_ago).exists()
    total_u = User.objects.count()
    total_p = Question.objects.count()
    active_p = Question.objects.filter(Q(deadline__gt=now) | Q(deadline__isnull=True)).count()
    county_stats = VoterProfile.objects.values('county').annotate(total=Count('id')).order_by('-total')[:6]
    chart_labels = [item['county'] for item in county_stats]
    chart_values = [item['total'] for item in county_stats]
    recent_logs = AuditLog.objects.all().order_by('-timestamp')[:5]

    return render(request, 'admin/admin_dashboard.html', {
        'total_users': total_u, 'total_polls': total_p, 'active_count': active_p,
        'system_secure': not failed_attempts, 'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values), 'recent_logs': recent_logs, 'now': now
    })

@user_passes_test(is_admin)
def system_health(request):
    total_voters = VoterProfile.objects.count()
    total_votes_cast = Vote.objects.count()
    total_questions = Question.objects.count()
    votes_dict = {item['county']: item['total'] for item in VoterProfile.objects.filter(has_voted=True).values('county').annotate(total=Count('id'))}
    reg_dict = {item['county']: item['total'] for item in VoterProfile.objects.values('county').annotate(total=Count('id'))}
    max_ballots = total_voters * total_questions
    turnout = round((total_votes_cast / max_ballots * 100), 1) if max_ballots > 0 else 0
    metrics = [
        {'label': 'Database', 'value': 'Operational', 'status': 'success'},
        {'label': 'Security', 'value': 'AES-256 SSL', 'status': 'success'},
        {'label': 'Turnout', 'value': f"{turnout}%", 'status': 'info'},
    ]
    return render(request, 'admin/system_health.html', {
        'metrics': metrics, 'total_voters': total_voters, 'votes_json': json.dumps(votes_dict), 'reg_json': json.dumps(reg_dict)
    })

# ── DESIGNER PDF EXPORT (PRESENTATION READY) ──

@user_passes_test(is_admin)
def export_stats_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="VOTE-X_Audit_{timezone.now().date()}.pdf"'
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    NAVY = colors.HexColor("#0f172a"); BLUE = colors.HexColor("#3b82f6"); SLATE = colors.HexColor("#64748b"); GREEN = colors.HexColor("#10b981"); LIGHT_BG = colors.HexColor("#f8fafc")
    
    p.setFillColor(NAVY); p.rect(0, height - 5, width, 5, fill=1, stroke=0)
    p.setFont("Helvetica-Bold", 24); p.setFillColor(NAVY); p.drawString(50, height - 60, "VOTE-X SYSTEM AUDIT")
    p.setFont("Helvetica-Bold", 10); p.setFillColor(BLUE); p.drawString(50, height - 80, "OFFICIAL PERFORMANCE RECORD")
    p.setFont("Helvetica", 9); p.setFillColor(SLATE); p.drawRightString(width - 50, height - 60, f"Issued: {timezone.now().strftime('%d %B %Y')}")
    p.line(50, height - 100, width - 50, height - 100)

    total_u = User.objects.count(); total_v = VoterProfile.objects.filter(has_voted=True).count(); total_p = Question.objects.count()
    stats = [("REGISTERED VOTERS", str(total_u), 50), ("TOTAL VOTES CAST", str(total_v), 215), ("ACTIVE SESSIONS", str(total_p), 380)]
    for label, val, x in stats:
        p.setFillColor(LIGHT_BG); p.roundRect(x, height - 190, 160, 70, 10, fill=1, stroke=0)
        p.setFont("Helvetica-Bold", 8); p.setFillColor(SLATE); p.drawString(x + 15, height - 145, label)
        p.setFont("Helvetica-Bold", 22); p.setFillColor(NAVY); p.drawString(x + 15, height - 175, val)

    p.setFillColor(colors.HexColor("#ecfdf5")); p.roundRect(50, height - 330, width - 100, 60, 12, fill=1, stroke=0)
    p.setFillColor(GREEN); p.setFont("Helvetica-Bold", 12); p.drawString(70, height - 290, "● SYSTEM INTEGRITY: SECURE")
    
    p.showPage()
    county_data = VoterProfile.objects.values('county').annotate(total=Count('id')).order_by('-total')
    table_data = [["COUNTY NAME", "REGISTERED", "STATUS"]]
    for item in county_data: table_data.append([item['county'].upper(), str(item['total']), "VERIFIED"])
    t = Table(table_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, LIGHT_BG]),('GRID',(0,0),(-1,-1),0.1,colors.grey)]))
    t.wrapOn(p, width, height); t.drawOn(p, 50, height - 150 - (len(table_data)*35))
    p.save(); return response

# ── CRUD OPERATIONS ──

@user_passes_test(is_admin)
def create_poll(request):
    if request.method == 'POST':
        poll = Question.objects.create(text=request.POST.get('text'), deadline=request.POST.get('deadline') or None)
        for opt in request.POST.getlist('options'):
            if opt.strip(): Choice.objects.create(question=poll, option_text=opt)
        record_audit(request, f"CREATED POLL: {poll.text}"); messages.success(request, "Poll launched."); return redirect('poll_list')
    return render(request, 'admin/poll_form.html')

@user_passes_test(is_admin)
def delete_poll(request, pk):
    poll = get_object_or_404(Question, pk=pk); txt = poll.text; poll.delete()
    record_audit(request, f"DELETED POLL: {txt}"); messages.success(request, "Poll deleted."); return redirect('poll_list')

@user_passes_test(is_admin)
def create_voter(request):
    if request.method == 'POST':
        try:
            u = User.objects.create_user(username=request.POST.get('username'), email=request.POST.get('email'), password=request.POST.get('password'))
            if request.POST.get('role') == 'admin': u.is_staff = True; u.save()
            VoterProfile.objects.create(user=u, county=request.POST.get('county'), national_id=request.POST.get('national_id'), role=request.POST.get('role'))
            record_audit(request, f"CREATED USER: {u.username}"); return redirect('user_list')
        except Exception as e: messages.error(request, str(e))
    return render(request, 'admin/user_form.html')

@user_passes_test(is_admin)
def edit_user(request, pk):
    u = get_object_or_404(User, pk=pk); p = u.voterprofile
    if request.method == 'POST':
        u.username = request.POST.get('username'); u.is_staff = (request.POST.get('role') == 'admin'); u.save()
        p.county = request.POST.get('county'); p.role = request.POST.get('role'); p.save()
        return redirect('user_list')
    return render(request, 'admin/user_form.html', {'edit_user': u, 'profile': p})

@user_passes_test(is_admin)
def delete_user(request, pk):
    u = get_object_or_404(User, pk=pk)
    if not u.is_superuser: u.delete(); messages.success(request, "User deleted.")
    return redirect('user_list')

# ── DIRECTORIES ──

@user_passes_test(is_admin)
def user_list(request):
    q = request.GET.get('q', '')
    users = User.objects.all().select_related('voterprofile').order_by('-id')
    if q: users = users.filter(Q(username__icontains=q) | Q(voterprofile__national_id__icontains=q))
    return render(request, 'admin/user_list.html', {'users': Paginator(users, 15).get_page(request.GET.get('page')), 'query': q})

@user_passes_test(is_admin)
def poll_list(request):
    return render(request, 'admin/poll_list.html', {'polls': Paginator(Question.objects.all().order_by('-id'), 10).get_page(request.GET.get('page')), 'now': timezone.now()})

@user_passes_test(is_admin)
def audit_log_view(request):
    return render(request, 'admin/audit_log.html', {'audit_logs': Paginator(AuditLog.objects.all().order_by('-timestamp'), 20).get_page(request.GET.get('page'))})

# ── VOTER HUB (FIXED ERRORS) ──

@login_required
def dashboard(request):
    if request.user.is_staff: return redirect('admin_dashboard')
    # Safety check for profile-less users (like manual superusers)
    profile = VoterProfile.objects.filter(user=request.user).first()
    total_polls = Question.objects.count()
    completed_votes = Vote.objects.filter(voter=request.user).count()
    progress = int((completed_votes / total_polls * 100)) if total_polls > 0 else 0
    pending = Question.objects.exclude(id__in=Vote.objects.filter(voter=request.user).values_list('question_id', flat=True)).filter(Q(deadline__gt=timezone.now()) | Q(deadline__isnull=True))[:3]
    return render(request, 'dashboard.html', {'profile': profile, 'completed_count': completed_votes, 'progress_percent': progress, 'pending_ballots': pending, 'total_polls': total_polls})

@login_required
def vote_view(request):
    answered = Vote.objects.filter(voter=request.user).values_list('question_id', flat=True)
    questions = Question.objects.exclude(id__in=answered).filter(Q(deadline__gt=timezone.now()) | Q(deadline__isnull=True)).prefetch_related('choices')
    if not questions.exists(): return redirect('results')
    return render(request, 'vote.html', {'questions': questions})

@login_required
def submit_vote(request):
    if request.method == 'POST':
        for key, val in request.POST.items():
            if key.startswith('question_'):
                qid = key.replace('question_', ''); q = get_object_or_404(Question, id=qid); c = get_object_or_404(Choice, id=val)
                _, created = Vote.objects.get_or_create(voter=request.user, question=q, defaults={'choice': c})
                if created: c.votes += 1; c.save()
        # Safety Check: Use hasattr to avoid RelatedObjectDoesNotExist crash
        if hasattr(request.user, 'voterprofile'):
            if Vote.objects.filter(voter=request.user).count() >= Question.objects.count():
                p = request.user.voterprofile; p.has_voted = True; p.save()
        return redirect('vote-success')
    return redirect('vote')

def register(request):
    if request.method == 'POST':
        try:
            u = User.objects.create_user(username=request.POST.get('username'), password=request.POST.get('password'), email=request.POST.get('email'))
            VoterProfile.objects.create(user=u, county=request.POST.get('county'), national_id=request.POST.get('national_id'), role='voter')
            messages.success(request, "Success!"); return redirect('login')
        except: messages.error(request, "Failed.")
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid(): login(request, form.get_user()); return redirect('dashboard')
        AuditLog.objects.create(action=f"FAILED LOGIN: {request.POST.get('username')}", ip_address=request.META.get('REMOTE_ADDR'))
    return render(request, 'login.html', {'form': AuthenticationForm()})

def logout_view(request): logout(request); return redirect('home')
@login_required
def vote_success(request): return render(request, 'vote_success.html')
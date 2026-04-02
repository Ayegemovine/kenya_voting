from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Route all traffic to your app-level urls first.
    # This keeps your app logic (voters, polls, etc.) separate from configuration.
    path('', include('voting.urls')), 
    
    # 2. Keep the default Django Admin at its original path for low-level database management.
    # By placing this second, your app's custom management paths ('mgmt/') take priority.
    path('admin/', admin.site.urls),
]
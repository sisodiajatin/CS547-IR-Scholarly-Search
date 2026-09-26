from django.db.models import Count, Max, Min
from .models import Paper, SavedPaper


def workspace(request):
    stats = Paper.objects.aggregate(total=Count("id"), earliest=Min("published"), latest=Max("published"))
    return {
        "corpus": stats,
        "saved_count": SavedPaper.objects.filter(user=request.user).count() if request.user.is_authenticated else 0,
    }

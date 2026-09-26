from time import perf_counter
from urllib.parse import urlencode
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_safe, require_http_methods, require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import SearchForm, SignupForm
from .models import Paper, PaperRedirect, Profile, SavedPaper
from .services import search_papers
from .citations import bibtex
from .navigation import reader_return


def saved_ids(request):
    return set(SavedPaper.objects.filter(user=request.user).values_list("paper_id", flat=True)) if request.user.is_authenticated else set()


@require_http_methods(["GET", "HEAD", "POST"])
def search(request):
    if request.method == "POST":
        return redirect(reverse("resps") + "?" + urlencode({"q": request.POST.get("query", "")}))
    years = list(Paper.objects.exclude(published=None).annotate(year=ExtractYear("published"))
                 .values("year").annotate(count=Count("id")).order_by("-year")[:12])
    peak = max((item["count"] for item in years), default=1)
    for item in years:
        item["height"] = max(4, round(item["count"] / peak * 100))
    return render(request, "search.html", {
        "recent_papers": Paper.objects.all()[:5], "year_distribution": list(reversed(years)),
        "saved_ids": saved_ids(request),
    })


@require_http_methods(["GET", "HEAD", "POST"])
def resps(request):
    if request.method == "POST":
        return redirect(reverse("resps") + "?" + urlencode({
            "q": request.POST.get("query2", ""),
            "year": request.POST.get("pub_year", "").replace("All", ""),
        }))
    started = perf_counter()
    form = SearchForm(request.GET)
    query, year, sort = request.GET.get("q", "")[:300], None, "relevance"
    year_mode, match = "since", "any"
    papers = Paper.objects.none()
    if form.is_valid():
        query = form.cleaned_data["q"]
        year = form.cleaned_data["year"]
        sort = form.cleaned_data["sort"] or "relevance"
        year_mode = form.cleaned_data["year_mode"] or "since"
        match = form.cleaned_data["match"] or "any"
        papers = search_papers(query, year, sort, year_mode, match=match)
        if year and not query:
            sort = "newest"
    page = Paginator(papers, 10).get_page(request.GET.get("page"))
    # Evaluate the current page while measuring query execution.
    page.object_list = list(page.object_list)
    return render(request, "resps.html", {
        "form": form, "query": query, "year": year, "year_mode": year_mode, "sort": sort, "match": match, "papers": page,
        "elapsed": round((perf_counter() - started) * 1000),
        "querystring": urlencode({"q": query, "year": year or "", "sort": sort, "year_mode": year_mode, "match": match}),
        "saved_ids": saved_ids(request),
    })


def safe_return(request, fallback):
    target = request.POST.get("next", request.GET.get("next", ""))
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, require_https=request.is_secure()):
        return target
    return reverse(fallback)


@require_http_methods(["GET", "HEAD", "POST"])
def login(request):
    next_url = safe_return(request, "search")
    if request.user.is_authenticated:
        return redirect(next_url)
    form = AuthenticationForm(request, data=request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect(next_url)
    return render(request, "login.html", {"form": form, "next_url": next_url})


@require_POST
def logout(request):
    auth_logout(request)
    return redirect("search")


@require_http_methods(["GET", "HEAD", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("profile")
    form = SignupForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            Profile.objects.create(user=user, major=form.cleaned_data["major"])
        auth_login(request, user)
        return redirect("profile")
    return render(request, "signup.html", {"form": form})


@login_required
@require_safe
def profile(request):
    return render(request, "profile.html", {
        "profile": Profile.objects.filter(user=request.user).first(),
    })


def resolve_paper(pk):
    alias = PaperRedirect.objects.filter(old_id=pk).first()
    return get_object_or_404(Paper, pk=alias.paper_id if alias else pk)


@require_safe
def paper_detail(request, pk):
    paper = resolve_paper(pk)
    return_to, return_label = reader_return(request.GET.get("return_to", ""))
    if paper.pk != pk:
        target = reverse("paper_detail", args=[paper.pk])
        if "return_to" in request.GET:
            target += "?" + urlencode({"return_to": return_to})
        return redirect(target, permanent=True)
    return render(request, "paper_detail.html", {
        "paper": paper, "citation": bibtex(paper), "saved_ids": saved_ids(request),
        "return_to": return_to, "return_label": return_label,
    })


@require_safe
def paper_citation(request, pk):
    paper = resolve_paper(pk)
    response = HttpResponse(bibtex(paper), content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="scholarly-{paper.pk}.bib"'
    return response


@login_required
@require_POST
def save_paper(request, pk):
    action = request.POST.get("action")
    if action not in {"save", "remove"}:
        return HttpResponseBadRequest("Choose a valid save or remove action.")
    paper = resolve_paper(pk)
    if action == "remove":
        SavedPaper.objects.filter(user=request.user, paper=paper).delete()
    else:
        SavedPaper.objects.get_or_create(user=request.user, paper=paper)
    target = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        target = reverse("library")
    return redirect(target or reverse("library"))


@require_safe
def library(request):
    query = request.GET.get("q", "").strip()[:300]
    records = SavedPaper.objects.none()
    if request.user.is_authenticated:
        records = SavedPaper.objects.filter(user=request.user).select_related("paper")
        if query:
            records = records.filter(Q(paper__title__icontains=query) | Q(paper__authors__icontains=query))
    page = Paginator(records, 10).get_page(request.GET.get("page"))
    return render(request, "library.html", {
        "records": page, "query": query, "saved_ids": saved_ids(request),
        "querystring": urlencode({"q": query}),
    })

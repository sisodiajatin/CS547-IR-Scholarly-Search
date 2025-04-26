from django.shortcuts import render, HttpResponse, redirect
from search import models
from django.db import connections
from urllib.parse import urlencode
from django.core.paginator import Paginator
import json
from datetime import datetime

import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# nltk.download('punkt_tab')  # use punkt model
# search functions
def tokenize(text):
    tokens = word_tokenize(text)
    return tokens

def stemmer(tokens):
    stemmer = PorterStemmer()
    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    return stemmed_tokens


# fetch paper data from dataset
with connections['arxiv_papers'].cursor() as cursor:
    cursor.execute("SELECT id, title, summary, authors, published, url FROM papers")
    rows = cursor.fetchall()

processed_papers = []

for row in rows:
    paper_id = row[0]
    paper_title = row[1]
    paper_summary = row[2]
    paper_author = row[3]
    paper_published = row[4]
    paper_url = row[5]

    # Tokenize and stem title and summary
    title_tokens = stemmer(tokenize(paper_title.lower()))
    summary_tokens = stemmer(tokenize(paper_summary.lower()))
    author_tokens = stemmer(tokenize(paper_author.lower()))

    processed_papers.append({
        "id": paper_id,
        "title": paper_title,
        "summary": paper_summary,
        "authors": paper_author,
        "published": paper_published,
        "url": paper_url,
        "stemmed_title": title_tokens,
        "stemmed_summary": summary_tokens,
        "stemmed_author": author_tokens,}
    )

# tags
tags = {
    "cs": [
        "Artificial Intelligence",
        "Machine Learning",
        "Natural Language Processing",
        "Computer Vision",
        "Deep Learning",
        # "Algorithms and Data Structures",
        # "Cybersecurity",
        # "Blockchain",
        # "Quantum Computing",
        # "Internet of Things",
        # "Software Engineering",
        # "Human-Computer Interaction",
        # "Cloud Computing",
        # "Big Data",
        # "Operating Systems"
    ],
    "ds": [
        "Data Mining",
        "Data Analytics",
        "Predictive Modeling",
        "Neural Networks",
        "Data Visualization",
        # "Statistical Learning",
        # "Reinforcement Learning",
        # "Bayesian Methods",
        # "Python/R for Data Science",
        # "Data Wrangling",
        # "High-Dimensional Data",
        # "Anomaly Detection",
        # "A/B Testing",
        # "Feature Engineering",
        # "Graph Analytics"
    ],
    "ms": [
        "Abstract Algebra",
        "Differential Equations",
        "Linear Algebra",
        "Calculus of Variations",
        "Topology",
        # "Number Theory",
        # "Combinatorics",
        # "Optimization",
        # "Probability Theory",
        # "Stochastic Processes",
        # "Game Theory",
        # "Functional Analysis",
        # "Numerical Methods",
        # "Cryptography",
        # "Mathematical Modeling"
    ],
    "ece": [
        "Embedded Systems",
        "Signal Processing",
        "Circuit Design",
        "Wireless Communications",
        "Antennas and Propagation",
        # "Power Systems",
        # "Microelectronics",
        # "Control Systems",
        # "Semiconductor Devices",
        # "Very Large Scale Integration",
        # "Micro-Electro-Mechanical Systems",
        # "Renewable Energy Systems",
        # "Photonics",
        # "Robotics and Automation",
        # "Network-on-Chip"
    ]
}

# for evaluation
def evaluate_search(query, results, top_k=10):
    query_tokens = tokenize(query.lower())
    stemmed_query = stemmer(query_tokens)

    relevance_count = 0
    coverage_count = 0
    dcg = 0
    idcg = sum(1.0 / (i + 1) for i in range(min(top_k, len(stemmed_query))))  # Ideal DCG

    for rank, paper in enumerate(results[:top_k]):
        score = sum(1 for token in stemmed_query if token in paper["stemmed_title"] + paper["stemmed_summary"])
        if score > 0:
            relevance_count += 1
            dcg += 1.0 / (rank + 1)  # Discounted gain

        coverage_count += sum(
            1 for token in stemmed_query if token in paper["stemmed_title"] + paper["stemmed_summary"])

    relevance = relevance_count / len(results) if results else 0
    ranking_quality = dcg / idcg if idcg > 0 else 0
    query_coverage = coverage_count / len(stemmed_query) if stemmed_query else 0

    return {
        "query": query,
        "relevance": relevance,
        "ranking_quality": ranking_quality,
        "query_coverage": query_coverage
    }

def log_evaluation(evaluation, filename="search_evaluation.log"):
    with open(filename, "a") as log_file:
        log_file.write(json.dumps(evaluation, indent=4) + "\n")


# Create your views here.

def search(request):
    if request.method == "GET":
        # redirect to the login page
        return render(request, "search.html")

    username = request.session.get('username')
    query = request.POST.get("query")
    tokens = tokenize(query)
    stemmed_tokens = stemmer(tokens)

    query_params = urlencode({'tokens': ','.join(stemmed_tokens)})
    request.session['current_query'] = query
    request.session['pub_year'] = "All"
    return redirect(f"/resps?{query_params}")

def resps(request):
    username = request.session.get('username')
    query = request.POST.get("query2")
    pub_year = request.POST.get("pub_year")

    if pub_year:
        if pub_year == "All":
            init_year = 0
        else:
            init_year = int(pub_year)
    else:
        init_year = 0

    if query:
        tokens = tokenize(query)
        stemmed_tokens = stemmer(tokens)
        ranked_papers = []
        ranked_papers2 = []

        # Search and rank papers based on token matches
        for paper in processed_papers:
            # Calculate relevance score
            title_matches = sum(1 for token in stemmed_tokens if token in paper["stemmed_title"])
            summary_matches = sum(1 for token in stemmed_tokens if token in paper["stemmed_summary"])
            author_matches = sum(1 for token in stemmed_tokens if token in paper["stemmed_author"])
            tags_score = 0

            if username:
                user = models.umTester.objects.filter(username=username).first()
                for i in tags[user.major]:
                    tag_token = stemmer(tokenize(i))
                    tags_title_score = sum(1 for token in tag_token if token in paper["stemmed_title"])
                    tags_score += tags_title_score

                    tags_summary_score = sum(1 for token in tag_token if token in paper["stemmed_summary"])
                    tags_score += tags_summary_score

            # total_matches = title_matches * 2 + summary_matches + author_matches # Weight title matches more heavily

            total_matches = title_matches + summary_matches + tags_score + author_matches
            pyear = int(paper["published"].year)

            if total_matches > 0 and pyear > init_year:
                ranked_papers.append({
                    "title": paper["title"],
                    "url": paper["url"],
                    "published": paper["published"],
                    "summary": paper["summary"],
                    "score": total_matches
                })

                ranked_papers2.append({"paper": paper, "score": total_matches})  # used for evaluation

        # Sort papers by relevance score (descending)
        ranked_papers.sort(key=lambda x: x["score"], reverse=True)

        # ==================evaluation=============================
        ranked_papers2.sort(key=lambda x: x["score"], reverse=True)
        results = [paper["paper"] for paper in ranked_papers2]

        # Evaluate search results
        evaluation = evaluate_search(query, results)
        evaluation["timestamp"] = datetime.now().isoformat()

        # Log evaluation
        log_evaluation(evaluation)
        # ==========================================================

        # Paginate results (10 papers per page)
        paginator = Paginator(ranked_papers, 10)
        page_number = request.GET.get('page', 1)  # Default to page 1 if no page number is provided
        page_obj = paginator.get_page(page_number)

        request.session['current_query'] = query

        return render(request, "resps.html", {
            "username": username,
            "papers": page_obj,  # Pass paginated papers to template
        })

    query = request.session.get('current_query')
    tokens = tokenize(query)
    stemmed_tokens = stemmer(tokens)

    ranked_papers = []
    ranked_papers2 = []

    # Search and rank papers based on token matches
    for paper in processed_papers:
        # Calculate relevance score
        title_matches = sum(1 for token in stemmed_tokens if token in paper["stemmed_title"])
        summary_matches = sum(1 for token in stemmed_tokens if token in paper["stemmed_summary"])
        author_matches = sum(1 for token in stemmed_tokens if token in paper["stemmed_author"])
        tags_score = 0

        if username:
            user = models.umTester.objects.filter(username=username).first()
            for i in tags[user.major]:
                tag_token = stemmer(tokenize(i))
                tags_title_score = sum(1 for token in tag_token if token in paper["stemmed_title"])
                tags_score += tags_title_score

                tags_summary_score = sum(1 for token in tag_token if token in paper["stemmed_summary"])
                tags_score += tags_summary_score

        # total_matches = title_matches * 2 + summary_matches + author_matches  # Weight title matches more heavily

        total_matches = title_matches + summary_matches + tags_score + author_matches
        pyear = int(paper["published"].year)

        if total_matches > 0 and pyear > init_year:
            ranked_papers.append({
                "title": paper["title"],
                "url": paper["url"],
                "published": paper["published"],
                "summary": paper["summary"],
                "score": total_matches
            })

            ranked_papers2.append({"paper": paper, "score": total_matches}) # used for evaluation

    # Sort papers by relevance score (descending)
    ranked_papers.sort(key=lambda x: x["score"], reverse=True)

    # ==================evaluation=============================
    ranked_papers2.sort(key=lambda x: x["score"], reverse=True)
    results = [paper["paper"] for paper in ranked_papers2]

    # Evaluate search results
    evaluation = evaluate_search(query, results)
    evaluation["timestamp"] = datetime.now().isoformat()

    # Log evaluation
    log_evaluation(evaluation)
    # ==========================================================

    # Paginate results (10 papers per page)
    paginator = Paginator(ranked_papers, 10)
    page_number = request.GET.get('page', 1)  # Default to page 1 if no page number is provided
    page_obj = paginator.get_page(page_number)

    request.session['current_query'] = query

    return render(request, "resps.html", {
        "username": username,
        "papers": page_obj,  # Pass paginated papers to template
    })

def login(request):
    if request.method == "GET":
        # redirect to the login page
        return render(request, "login.html")
    # the method is POST
    # get data provided by users
    username = request.POST.get("user")
    password = request.POST.get("pwd")

    user = models.umTester.objects.filter(username=username, password=password).first()
    # login successfully

    if user:
        request.session['username'] = user.username # Save to session
        return render(request, "search.html")

    # Invalid username or password
    return render(request, "login.html", {"error_msg": "Invalid Username or Password. Please try again."})

def logout(request):
    # Clear the username from the session
    # request.session['username'] = None
    # Optionally, clear the entire session
    request.session.flush()
    return render(request, "search.html")  # Redirect to the search page

def signup(request):
    # sign up operation
    if request.method == "GET":
        # redirect to the sign up page
        return render(request, "signup.html")

    # get data provided by users
    username = request.POST.get("user2")
    password = request.POST.get("pwd2")
    major = request.POST.get("major")

    user_list = models.umTester.objects.all()

    if models.umTester.objects.filter(username=username).exists():
        return render(request, "signup.html", {"error_msg": "Existing Username. Please try again."})
    else:
        models.umTester.objects.create(username=username, password=password, major=major)

    # return to login page
    return render(request, "login.html")

def profile(request):
    # Check if the user is logged in
    username = request.session.get('username')
    if not username:
        # Redirect to login if not logged in
        return render(request, 'login.html')

    # Query user information
    user = models.umTester.objects.filter(username=username).first()

    if not user:
        # Handle the edge case where the user does not exist (optional)
        return render(request, 'login.html')

    # Pass only username and major to the template
    return render(request, 'profile.html', {
        'username': user.username,
        'major': user.major,
    })


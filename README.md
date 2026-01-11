# CS547-IR Scholarly Search

## 📚 Overview

This project is a scholarly search web application developed for the **CS547 Information Retrieval** course. It mimics platforms like Google Scholar and arXiv by allowing users to search academic papers using keywords. The system supports user authentication, query-based search, and returns ranked results based on relevance.

---

## 🔍 Features

- 🔑 **User Authentication** – Register and log in.
- 🔎 **Keyword Search** – Search by title, abstract, or author names.
- 📄 **Metadata Display** – View paper title, authors, abstract, publication date, and direct URL.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.13.1, Django 5.1.4  
- **Frontend**: Django templates (HTML, CSS)  
- **Database**: SQLite3 (with preloaded arXiv papers)

---

## 🗂️ Dataset Schema

| Field      | Type   | Description                        |
|------------|--------|------------------------------------|
| id         | INT    | Unique ID for each paper           |
| title      | TEXT   | Title of the paper                 |
| abstract   | TEXT   | Abstract content                   |
| authors    | TEXT   | Comma-separated author list        |
| published  | DATE   | Date of publication                |
| url        | TEXT   | Direct link to arXiv or reference  |

---

## 🚀 Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/sisodiajatin/CS547-IR-Scholarly-Search.git
   cd CS547-IR-Scholarly-Search
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv env
   source env/bin/activate  # Windows: env\Scripts\activate
   ```

3. **Install the required packages**

4. **Apply migrations and load data**
   ```bash
   python manage.py migrate
   python manage.py loaddata arxiv_papers.sql
   ```

5. **Run the Django development server**
   ```bash
   python manage.py runserver
   ```

6. **Open the application**
   - Visit: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---


## 🤝 Contributions

We welcome contributions!  
Feel free to fork this repo, suggest improvements, or open issues.

---

## 📄 License

Licensed under the [MIT License](LICENSE).

---

## 📬 Contact

Created by [@sisodiajatin](https://github.com/sisodiajatin)  
For feedback or collaboration, feel free to reach out!

---

**Happy Searching!** 🚀



"""Export only metadata present in the source corpus."""


def tex(value):
    escapes = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
               "%": r"\%", "&": r"\&", "_": r"\_", "#": r"\#",
               "$": r"\$", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(escapes.get(char, char) for char in " ".join(value.split()))


def bibtex(paper):
    authors = " and ".join(tex(author.strip()) for author in paper.authors.split(",") if author.strip())
    fields = [f"  title = {{{tex(paper.title)}}}", f"  author = {{{authors}}}"]
    if paper.published:
        fields.append(f"  year = {{{paper.published.year}}}")
    fields.append(f"  url = {{{tex(paper.url)}}}")
    return f"@misc{{scholarly{paper.pk},\n" + ",\n".join(fields) + "\n}\n"

"""Render selected public notebooks as static pages without executing code."""

from __future__ import annotations

import html
import hashlib
import json
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import nbformat
from nbconvert import HTMLExporter


ROOT = Path(__file__).resolve().parents[1]
OWNER = "YuxuanZhao-Econ"


@dataclass(frozen=True)
class NotebookPage:
    repository: str
    source_path: str
    output_path: str
    title: str
    description: str

    @property
    def source_url(self) -> str:
        return f"https://github.com/{OWNER}/{self.repository}/blob/main/{self.source_path}"

    @property
    def raw_url(self) -> str:
        return f"https://raw.githubusercontent.com/{OWNER}/{self.repository}/main/{self.source_path}"


NOTEBOOKS = (
    NotebookPage(
        repository="DeepLearningMacro",
        source_path="notebooks/Intro_DL.ipynb",
        output_path="notebooks/deep-learning-macro/intro-to-deep-learning/index.html",
        title="Intro to Deep Learning",
        description="Neural-network foundations and automatic differentiation for computational macroeconomics.",
    ),
    NotebookPage(
        repository="DeepLearningMacro",
        source_path="notebooks/RBC.ipynb",
        output_path="notebooks/deep-learning-macro/rbc-model/index.html",
        title="Deep Learning for an RBC Model",
        description="An Euler-equation deep-learning method applied to a stochastic RBC benchmark.",
    ),
    NotebookPage(
        repository="DeepLearningMacro",
        source_path="notebooks/KS1998.ipynb",
        output_path="notebooks/deep-learning-macro/krusell-smith/index.html",
        title="Deep Learning for the Krusell–Smith Model",
        description="A deep-learning Euler-equation method for the Krusell–Smith heterogeneous-agent model.",
    ),
    NotebookPage(
        repository="sequence_space_jacobian",
        source_path="notebooks/KS1998.ipynb",
        output_path="notebooks/sequence-space-jacobian/krusell-smith/index.html",
        title="Krusell–Smith with Sequence-Space Jacobians",
        description="A heterogeneous-agent transition exercise using sequence-space Jacobians and the fake news algorithm.",
    ),
    NotebookPage(
        repository="sequence_space_jacobian",
        source_path="notebooks/RBC.ipynb",
        output_path="notebooks/sequence-space-jacobian/rbc-model/index.html",
        title="RBC Model with Sequence-Space Jacobians",
        description="A compact introduction to solving an RBC model with sequence-space Jacobians in Julia.",
    ),
    NotebookPage(
        repository="HANK",
        source_path="notebooks/HANK.ipynb",
        output_path="notebooks/hank/index.html",
        title="Solving a HANK Model",
        description="A global solution of a one-asset heterogeneous-agent New Keynesian model with aggregate TFP and monetary-policy shocks.",
    ),
    NotebookPage(
        repository="KS1998",
        source_path="notebooks/KS1998_Solver.ipynb",
        output_path="notebooks/ks1998/solver/index.html",
        title="Krusell–Smith (1998) Solver",
        description="A Julia implementation of the traditional Krusell–Smith (1998) solution algorithm.",
    ),
)


def download_notebook(page: NotebookPage):
    request = urllib.request.Request(
        page.raw_url,
        headers={"User-Agent": "Yuxuan-Zhao-notebook-publisher"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        raw = response.read().decode("utf-8")

    # Older notebooks may not contain cell IDs. Assign stable IDs before
    # nbformat validation so unchanged notebooks render identically every run.
    payload = json.loads(raw)
    for index, cell in enumerate(payload.get("cells", [])):
        if cell.get("id"):
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        fingerprint = f"{index}\0{cell.get('cell_type', '')}\0{source}"
        digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
        cell["id"] = f"cell-{digest}"

    return nbformat.reads(json.dumps(payload, ensure_ascii=False), as_version=4)


def remove_duplicate_title(notebook) -> None:
    for cell in notebook.cells:
        if cell.cell_type != "markdown":
            continue
        lines = cell.source.splitlines()
        first_content = next((i for i, line in enumerate(lines) if line.strip()), None)
        if first_content is not None and lines[first_content].lstrip().startswith("# "):
            del lines[first_content]
            cell.source = "\n".join(lines).lstrip()
        break


def notebook_body(notebook) -> tuple[str, str]:
    exporter = HTMLExporter(template_name="basic")
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    exporter.anchor_link_text = ""
    body, resources = exporter.from_notebook_node(notebook)
    inline_css = "\n".join(resources.get("inlining", {}).get("css", []))
    return body, inline_css


def render_page(page: NotebookPage, body: str, inline_css: str, kernel: str) -> str:
    title = html.escape(page.title)
    description = html.escape(page.description)
    repository = html.escape(page.repository)
    source_url = html.escape(page.source_url, quote=True)
    canonical = f"https://www.yuxuan-zhao.com/{page.output_path.removesuffix('index.html')}"
    kernel_label = html.escape(kernel or "Julia")

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{description}" />
    <meta name="theme-color" content="#f7f5ef" />
    <link rel="canonical" href="{canonical}" />
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet" />
    <style>{inline_css}</style>
    <link rel="stylesheet" href="/notebooks/notebook.css" />
    <script>
      window.MathJax = {{ tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] }}, options: {{ skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }} }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" defer></script>
    <script src="/notebooks/notebook.js" defer></script>
    <title>{title} — Yuxuan Zhao</title>
  </head>
  <body class="notebook-page">
    <a class="skip-link" href="#notebook-content">Skip to notebook</a>
    <header class="notebook-header">
      <div class="notebook-header-inner">
        <a class="wordmark" href="/">Yuxuan <span>/</span> Economics</a>
        <a class="library-link" href="/notebooks/">Notebook library</a>
      </div>
    </header>

    <main class="notebook-shell">
      <nav class="notebook-utility" aria-label="Notebook links">
        <a href="/">← Back to website</a>
        <span aria-hidden="true">·</span>
        <a href="{source_url}" target="_blank" rel="noreferrer">View source ↗</a>
      </nav>

      <header class="notebook-title-block">
        <p class="notebook-repository">{repository}</p>
        <h1>{title}</h1>
        <p class="notebook-description">{description}</p>
        <p class="notebook-meta">{kernel_label} notebook · Static rendering · Code was not re-executed</p>
      </header>

      <article class="notebook-content" id="notebook-content">
{body}
      </article>
    </main>

    <footer class="notebook-footer">
      <div><span>Yuxuan Zhao</span><a href="/notebooks/">Browse all notebooks →</a></div>
    </footer>
  </body>
</html>
"""


def main() -> int:
    for page in NOTEBOOKS:
        print(f"Rendering {page.repository}/{page.source_path}")
        notebook = download_notebook(page)
        remove_duplicate_title(notebook)
        body, inline_css = notebook_body(notebook)
        kernel = notebook.metadata.get("kernelspec", {}).get("display_name", "Julia")
        output = ROOT / page.output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_page(page, body, inline_css, kernel), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

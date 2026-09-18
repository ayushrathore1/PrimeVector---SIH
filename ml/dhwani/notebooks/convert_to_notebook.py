"""
Convert dhwani_training.py (with # %% cell markers) to a proper
Jupyter .ipynb notebook for direct upload to Google Colab.

Usage:
    python convert_to_notebook.py

Output:
    ml/dhwani/notebooks/Dhwani_Training.ipynb
"""
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "dhwani_training.py")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "Dhwani_Training.ipynb")


def py_to_ipynb(py_path: str, ipynb_path: str):
    """Convert a .py file with # %% markers to .ipynb format."""
    with open(py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by cell markers
    # Patterns: "# %%", "# %% [markdown]"
    cell_pattern = re.compile(r'^# %%(?:\s+\[markdown\])?\s*$', re.MULTILINE)
    parts = cell_pattern.split(content)

    # Find marker positions to determine cell types
    markers = cell_pattern.findall(content)

    cells = []

    # First part before any marker (module docstring) → skip or make markdown
    if parts[0].strip():
        # Convert module docstring to markdown
        docstring = parts[0].strip()
        # Remove leading/trailing triple quotes and comment chars
        lines = docstring.split("\n")
        md_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                md_lines.append(stripped.lstrip("# "))
            elif stripped:
                md_lines.append(stripped)
        if md_lines:
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [l + "\n" for l in md_lines],
            })

    # Process remaining parts
    for i, part in enumerate(parts[1:], start=0):
        if not part.strip():
            continue

        # Determine cell type based on the marker
        if i < len(markers) and "[markdown]" in markers[i]:
            # Markdown cell — strip leading # from each line
            lines = part.strip().split("\n")
            md_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#"):
                    md_lines.append(stripped.lstrip("# "))
                elif stripped == "":
                    md_lines.append("")
                else:
                    md_lines.append(stripped)
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [l + "\n" for l in md_lines],
            })
        else:
            # Code cell
            source_lines = part.rstrip("\n").split("\n")
            # Remove leading empty lines
            while source_lines and not source_lines[0].strip():
                source_lines.pop(0)

            if source_lines:
                cells.append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [l + "\n" for l in source_lines],
                })

    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10.0",
            },
            "colab": {
                "provenance": [],
                "gpuType": "T4",
            },
            "accelerator": "GPU",
        },
        "cells": cells,
    }

    with open(ipynb_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"[OK] Converted {py_path}")
    print(f"   -> {ipynb_path}")
    print(f"   {len(cells)} cells ({sum(1 for c in cells if c['cell_type'] == 'code')} code, "
          f"{sum(1 for c in cells if c['cell_type'] == 'markdown')} markdown)")


if __name__ == "__main__":
    py_to_ipynb(INPUT_FILE, OUTPUT_FILE)

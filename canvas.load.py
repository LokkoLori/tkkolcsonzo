import sys
import re
from pathlib import Path


# sys.exit(0)  # this is dangerous code

# Path to your downloaded canvas file
doc_path = Path("./canvas.txt")  # modify if different
# Base directory for project output
output_base = Path(".")

# Regex to match code blocks: e.g. ## filename + ```lang ... ```
section_pattern = re.compile(r"^## (.+?)\n```.*?\n(.*?)```", re.DOTALL | re.MULTILINE)

with open(doc_path, "r", encoding="utf-8") as f:
    text = f.read()

for match in section_pattern.finditer(text):
    rel_path = match.group(1).strip()
    content = match.group(2).strip("\n")
    # skip non-files like 'Project layout'
    if not any(ext in rel_path for ext in [".py", ".html", ".txt", ".gitignore"]):
        continue

    file_path = output_base / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as out:
        out.write(content + "\n")
    print(f"✓ Wrote {file_path}")

print("All files extracted.")
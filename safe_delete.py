import ast, sys
from pathlib import Path
import subprocess

dead = ["set_language","open_url","get_current_context","push_context","pop_context","resolve_color_default","isolated_filesystem","term_len","join_options","readable"]

for py in Path("src").rglob("*.py"):
    src = py.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except:
        continue
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in dead:
            lines = src.splitlines(True)
            start = node.lineno - 1
            end = node.end_lineno
            new_src = "".join(lines[:start] + lines[end:])
            py.write_text(new_src, encoding="utf-8")
            print(f"trying delete {node.name} from {py}")
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x"], capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                print(f"[OK] kept deletion of {node.name}")
            else:
                py.write_text(src, encoding="utf-8")
                print(f"[FAIL] reverted {node.name}")
            break

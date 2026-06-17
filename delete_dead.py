import re
from pathlib import Path

# functions Reality OS proved dead
dead = ["get_command","resolve_command","it","set_language","list_commands","convert","new_func","argument","option","confirmation_option","callback","password_option","version_option","help_option","show_help","write","section","indentation","getvalue","join_options","get_current_context","push_context","pop_context","resolve_color_default","name","isolated_filesystem","readable","term_len","func","generator","open_url","readinto","add_alias","read_config","write_config","alias","get_env_vars","list_users","process_commands","processor","copy_filename","open_cmd","save_cmd","resize_cmd","crop_cmd","convert_rotation","convert_flip","transpose_cmd","smoothen_cmd","paste_cmd","ship_move","ship_shoot","mine_set","set_config","setuser","copy","progress","process_slowly","filter","show_item","validate_count","log","vlog"]

for py in Path("src").rglob("*.py"):
    text = py.read_text(encoding="utf-8", errors="ignore")
    orig = text
    for fn in dead:
        # delete def fn(...): ... (simple heuristic)
        text = re.sub(rf"\n def {fn}\(.*? \):(?:\n [ ]{{4}}.*)+", "", text, flags=re.DOTALL)
        text = re.sub(rf"\n    def {fn}\(.*? \):(?:\n        .*)+", "", text, flags=re.DOTALL)
    if text != orig:
        py.write_text(text, encoding="utf-8")
        print(f"cleaned {py}")

import subprocess
import os

repo_path = r"m:\claim360_email_webapp\claim360"
output_file = r"m:\claim360_email_webapp\claim360\git_info.txt"

commands = [
    "git status",
    "git diff backend/core/database.py",
    "git log -n 5 --oneline"
]

with open(output_file, "w") as f:
    for cmd in commands:
        f.write(f"--- Running: {cmd} ---\n")
        try:
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, shell=True)
            f.write(result.stdout)
            f.write(result.stderr)
        except Exception as e:
            f.write(f"Error running command: {str(e)}\n")
        f.write("\n\n")

print(f"Done! Created {output_file}")

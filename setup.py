import os
import subprocess
import sys

# Path to your frappe/bench directory
BENCH_DIR = "../../"

# Path to your venv inside bench (expand ~ to full path)
VENV_PATH = os.path.expanduser("~/.venv/cenv/bin/activate")

# Your site name
SITE_NAME = "msite.local"   # <-- change this to your site

# Administrator API key and secret
ADMIN_API_KEY = "0909"
ADMIN_API_SECRET = "1212"

def run_command(command, cwd=None, env=None):
    """Helper to run shell commands and stream output"""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        executable="/bin/bash"
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        sys.exit(process.returncode)

def main():
    activate_cmd = f"source {VENV_PATH}"

    # Step 1: enable developer_mode
    run_command(f"{activate_cmd} && bench set-config developer_mode 1", cwd=BENCH_DIR)

    # Step 2: enable server_script_enabled
    run_command(f"{activate_cmd} && bench set-config server_script_enabled true", cwd=BENCH_DIR)

    # Step 3: set Administrator API key/secret using bench execute with inline python
    api_cmd = f"""{activate_cmd} && bench --site {SITE_NAME} execute "exec(\\"import frappe; \
frappe.connect(); \
user=frappe.get_doc('User','Administrator'); \
user.api_key='{ADMIN_API_KEY}'; \
user.api_secret='{ADMIN_API_SECRET}'; \
user.save(ignore_permissions=True); \
frappe.db.commit(); \
print('✅ API credentials set for Administrator')\\")"
"""
    run_command(api_cmd, cwd=BENCH_DIR)

if __name__ == "__main__":
    main()

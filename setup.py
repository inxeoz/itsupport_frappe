import os
import subprocess
import sys
from getpass import getpass


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


def enable_developer_mode(activate_cmd, bench_dir):
    run_command(f"{activate_cmd} && bench set-config developer_mode 1", cwd=bench_dir)
    print("✅ Developer mode enabled")


def enable_server_scripts(activate_cmd, bench_dir):
    run_command(f"{activate_cmd} && bench set-config server_script_enabled true", cwd=bench_dir)
    print("✅ Server scripts enabled")


def set_admin_api_keys(activate_cmd, bench_dir, site_name, api_key, api_secret):
    api_cmd = f"""{activate_cmd} && bench --site {site_name} execute "exec(\\"import frappe; \
frappe.connect(); \
user=frappe.get_doc('User','Administrator'); \
user.api_key='{api_key}'; \
user.api_secret='{api_secret}'; \
user.save(ignore_permissions=True); \
frappe.db.commit(); \
print('✅ API credentials set for Administrator')\\")"
"""
    run_command(api_cmd, cwd=bench_dir)


def update_admin_password(activate_cmd, bench_dir, site_name):
    new_password = os.getenv("ADMIN_PASSWORD") or getpass("Enter new Administrator password: ")

    password_cmd = f"""{activate_cmd} && bench --site {site_name} execute "exec(\\"import frappe; \
frappe.connect(); \
from frappe.utils import password as _password; \
_password.update_password('Administrator', '{new_password}'); \
frappe.db.commit(); \
print('✅ Password updated for Administrator')\\")"
"""
    run_command(password_cmd, cwd=bench_dir)


def set_cors(activate_cmd, bench_dir):
    print("\nCORS Configuration:")
    print("1. Allow all origins")
    print("2. Enter custom origin(s)")
    print("3. Disable CORS")
    choice = input("Select option (1/2/3): ").strip()

    if choice == "1":
        run_command(f"{activate_cmd} && bench set-config allow_cors '*'", cwd=bench_dir)
        print("✅ CORS set to allow all origins")
    elif choice == "2":
        origins = input("Enter allowed origin(s) (comma-separated): ").strip()
        run_command(f"{activate_cmd} && bench set-config allow_cors '{origins}'", cwd=bench_dir)
        print(f"✅ CORS set to: {origins}")
    elif choice == "3":
        run_command(f"{activate_cmd} && bench set-config -r allow_cors", cwd=bench_dir)
        print("✅ CORS disabled")
    else:
        print("⚠️ Invalid choice, skipping CORS configuration")


def main():
    # Ask for paths, with defaults
    bench_dir = input("Enter bench directory [../../]: ").strip() or "../../"
    venv_path = input("Enter virtualenv path [~/.venv/cenv/bin/activate]: ").strip() or "~/.venv/cenv/bin/activate"
    site_name = input("Enter site name [msite.local]: ").strip() or "msite.local"

    activate_cmd = f"source {os.path.expanduser(venv_path)}"

    # Ask whether to enable developer mode
    if input("Enable developer mode? (y/n): ").lower().strip() == "y":
        enable_developer_mode(activate_cmd, bench_dir)

    # Ask whether to enable server scripts
    if input("Enable server scripts? (y/n): ").lower().strip() == "y":
        enable_server_scripts(activate_cmd, bench_dir)

    # Ask for API key/secret
    api_key = input("Enter Administrator API key: ").strip()
    api_secret = getpass("Enter Administrator API secret: ")
    set_admin_api_keys(activate_cmd, bench_dir, site_name, api_key, api_secret)

    # Update admin password
    update_admin_password(activate_cmd, bench_dir, site_name)

    # Ask for CORS config
    set_cors(activate_cmd, bench_dir)


if __name__ == "__main__":
    main()

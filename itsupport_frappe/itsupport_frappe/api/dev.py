
# import subprocess
# import frappe
# import os

# @frappe.whitelist()
# def build_static_ui():
#     try:
#         app_path = frappe.get_app_path('itsupport_frappe')
#         frontend_path = os.path.join(app_path, 'itsupport_react')

#         # Run build and wait until it completes
#         result = subprocess.run(["npx", "vite", "build"], cwd=frontend_path, capture_output=True, text=True)

#         if result.returncode == 0:
#             return {"status": "success", "output": result.stdout}
#         else:
#             return {"status": "error", "message": result.stderr}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}



import subprocess
import frappe
import os

LAST_COMMIT_FILE = "last_commit"

def get_latest_commit_hash(main_dir):
    """Return the latest commit hash in main_dir."""
    result = subprocess.run(
        ["git", "log", "-n", "1", "--pretty=format:%H", "--", "."],
        cwd=main_dir,
        capture_output=True,
        text=True
    )
    return result.stdout.strip() if result.returncode == 0 else None

def get_commit_file_path(current_dir):
    """Return the path to the last_commit file."""
    return os.path.join(current_dir, LAST_COMMIT_FILE)

def read_last_commit(current_dir):
    """Read the last commit hash from file, if it exists."""
    file_path = get_commit_file_path(current_dir)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read().strip()
    return None

def write_last_commit(current_dir, commit_hash):
    """Write the latest commit hash to file."""
    file_path = get_commit_file_path(current_dir)
    with open(file_path, "w") as f:
        f.write(commit_hash)

def needs_build(main_dir, current_dir):
    """
    Checks commit hash and updates file.
    Returns:
        "first_build" (if last_commit did not exist),
        "need_build" (if commit changed),
        "skip_build" (if commit is same),
        "error" (if something is wrong)
    """
    latest_commit = get_latest_commit_hash(main_dir)
    if not latest_commit:
        return "error"
    last_commit = read_last_commit(current_dir)
    if last_commit is None:
        write_last_commit(current_dir, latest_commit)
        return "first_build"
    if latest_commit != last_commit:
        write_last_commit(current_dir, latest_commit)
        return "need_build"
    # return "need_build"
    return "skip_build"

@frappe.whitelist()
def build_static_ui():
    try:
        app_path = frappe.get_app_path('itsupport_frappe')
        main_dir = os.path.join(app_path, 'itsupport_react')
        current_dir = os.getcwd()

        build_status = needs_build(main_dir, current_dir)

        if build_status == "error":
            return {"status": "error", "message": "No commit hash found for the main directory."}
        if build_status in ("first_build", "need_build"):
            result = subprocess.run(
                ["npx", "vite", "build"],
                cwd=main_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return {"status": "success", "output": result.stdout}
            else:
                return {"status": "error", "message": result.stderr}
        else:
            # build_status == "skip_build"
            return {"status": "success", "output": "skipped build"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

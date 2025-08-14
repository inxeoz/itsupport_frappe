
import subprocess
import frappe
import os

@frappe.whitelist()
def build_static_ui():
    try:
        app_path = frappe.get_app_path('itsupport_frappe')
        frontend_path = os.path.join(app_path, 'itsupport_react')

        # Run build and wait until it completes
        result = subprocess.run(["npx", "vite", "build"], cwd=frontend_path, capture_output=True, text=True)

        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}

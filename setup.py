#!/usr/bin/env python3
"""
Universal Frappe Bench Setup Script
Automatically detects bench configuration and sets up development environment
"""

import os
import subprocess
import sys
import json
import glob
from pathlib import Path
from getpass import getpass

class BenchSetup:
    def __init__(self):
        self.bench_dir = None
        self.venv_path = None
        self.python_path = None
        self.sites = []
        self.activate_cmd = None
        
    def find_bench_directory(self):
        """Auto-detect bench directory"""
        current_dir = Path.cwd()
        
        # Check current directory and parents for bench indicators
        for path in [current_dir] + list(current_dir.parents):
            if self.is_bench_directory(path):
                return str(path)
        
        # Common bench locations
        common_paths = [
            "~/frappe-bench",
            "~/bench",
            "~/erpnext",
            "/home/frappe/frappe-bench",
            "/opt/bench",
            "./",
            "../",
            "../../"
        ]
        
        for path in common_paths:
            expanded_path = Path(os.path.expanduser(path))
            if expanded_path.exists() and self.is_bench_directory(expanded_path):
                return str(expanded_path)
        
        return None
    
    def is_bench_directory(self, path):
        """Check if directory is a valid bench"""
        path = Path(path)
        required_files = ['sites', 'apps']
        return all((path / file).exists() for file in required_files)
    
    def find_python_executable(self, bench_dir):
        """Find the Python executable for this bench"""
        bench_path = Path(bench_dir)
        
        # Check for virtual environment
        venv_patterns = [
            bench_path / "env" / "bin" / "python",
            bench_path / "venv" / "bin" / "python", 
            bench_path / ".venv" / "bin" / "python",
            bench_path / "env" / "bin" / "python3",
            bench_path / "venv" / "bin" / "python3",
        ]
        
        for python_path in venv_patterns:
            if python_path.exists():
                return str(python_path)
        
        # Check system Python
        try:
            result = subprocess.run(['which', 'python3'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
            
        return sys.executable
    
    def find_activation_script(self, bench_dir):
        """Find virtual environment activation script"""
        bench_path = Path(bench_dir)
        
        activation_patterns = [
            bench_path / "env" / "bin" / "activate",
            bench_path / "venv" / "bin" / "activate",
            bench_path / ".venv" / "bin" / "activate"
        ]
        
        for activate_path in activation_patterns:
            if activate_path.exists():
                return f"source {activate_path}"
        
        return None
    
    def get_sites_list(self, bench_dir):
        """Get list of sites in the bench"""
        sites_dir = Path(bench_dir) / "sites"
        if not sites_dir.exists():
            return []
        
        sites = []
        for item in sites_dir.iterdir():
            if item.is_dir() and item.name not in ['common_site_config.json', 'assets']:
                # Check if it's a valid site by looking for site_config.json
                if (item / "site_config.json").exists():
                    sites.append(item.name)
        
        return sites
    
    def auto_detect_bench(self):
        """Auto-detect bench configuration"""
        print("🔍 Auto-detecting bench configuration...")
        
        # Find bench directory
        self.bench_dir = self.find_bench_directory()
        if not self.bench_dir:
            print("❌ Could not find bench directory automatically")
            self.bench_dir = input("Enter bench directory path: ").strip()
            if not self.bench_dir or not self.is_bench_directory(Path(self.bench_dir)):
                print("❌ Invalid bench directory")
                sys.exit(1)
        
        print(f"✅ Found bench directory: {self.bench_dir}")
        
        # Find Python and activation
        self.python_path = self.find_python_executable(self.bench_dir)
        self.activate_cmd = self.find_activation_script(self.bench_dir)
        
        if self.activate_cmd:
            print(f"✅ Found virtual environment: {self.activate_cmd.split()[-1]}")
        else:
            print("⚠️ No virtual environment found, using system Python")
            self.activate_cmd = ""
        
        # Get sites
        self.sites = self.get_sites_list(self.bench_dir)
        if self.sites:
            print(f"✅ Found sites: {', '.join(self.sites)}")
        else:
            print("⚠️ No sites found")
    
    def run_command(self, command, cwd=None, env=None):
        """Helper to run shell commands and stream output"""
        if cwd is None:
            cwd = self.bench_dir
            
        full_command = f"{self.activate_cmd} && {command}" if self.activate_cmd else command
        
        process = subprocess.Popen(
            full_command,
            cwd=cwd,
            env=env,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            executable="/bin/bash"
        )
        
        output = ""
        for line in process.stdout:
            print(line, end="")
            output += line
            
        process.wait()
        if process.returncode != 0:
            print(f"❌ Command failed with return code {process.returncode}")
            return False, output
        return True, output
    
    def enable_developer_mode(self):
        """Enable developer mode"""
        success, _ = self.run_command("bench set-config developer_mode 1")
        if success:
            print("✅ Developer mode enabled")
        return success
    
    def enable_server_scripts(self):
        """Enable server scripts"""
        success, _ = self.run_command("bench set-config server_script_enabled true")
        if success:
            print("✅ Server scripts enabled")
        return success
    
    def set_admin_api_keys(self, site_name, api_key, api_secret):
        """Set API credentials for Administrator"""
        api_cmd = f"""bench --site {site_name} execute "exec(\\"import frappe; \
frappe.connect(); \
user=frappe.get_doc('User','Administrator'); \
user.api_key='{api_key}'; \
user.api_secret='{api_secret}'; \
user.save(ignore_permissions=True); \
frappe.db.commit(); \
print('✅ API credentials set for Administrator')\\")\""""
        
        success, _ = self.run_command(api_cmd)
        return success
    
    def update_admin_password(self, site_name):
        """Update Administrator password"""
        new_password = os.getenv("ADMIN_PASSWORD") or getpass("Enter new Administrator password: ")
        
        password_cmd = f"""bench --site {site_name} execute "exec(\\"import frappe; \
frappe.connect(); \
from frappe.utils.password import update_password; \
update_password('Administrator', '{new_password}'); \
frappe.db.commit(); \
print('✅ Password updated for Administrator')\\")\""""
        
        success, _ = self.run_command(password_cmd)
        return success
    
    def set_cors(self):
        """Configure CORS settings"""
        print("\nCORS Configuration:")
        print("1. Allow all origins (*)")
        print("2. Enter custom origin(s)")
        print("3. Disable CORS")
        print("4. Skip CORS configuration")
        
        choice = input("Select option (1/2/3/4): ").strip()
        
        if choice == "1":
            success, _ = self.run_command("bench set-config allow_cors '*'")
            if success:
                print("✅ CORS set to allow all origins")
        elif choice == "2":
            origins = input("Enter allowed origin(s) (comma-separated): ").strip()
            if origins:
                success, _ = self.run_command(f"bench set-config allow_cors '{origins}'")
                if success:
                    print(f"✅ CORS set to: {origins}")
        elif choice == "3":
            success, _ = self.run_command("bench set-config -r allow_cors")
            if success:
                print("✅ CORS disabled")
        elif choice == "4":
            print("⏭️ Skipping CORS configuration")
        else:
            print("⚠️ Invalid choice, skipping CORS configuration")
    
    def select_site(self):
        """Select a site to work with"""
        if not self.sites:
            site_name = input("Enter site name: ").strip()
            if not site_name:
                print("❌ Site name is required")
                sys.exit(1)
            return site_name
        
        if len(self.sites) == 1:
            print(f"✅ Using site: {self.sites[0]}")
            return self.sites[0]
        
        print("\nAvailable sites:")
        for i, site in enumerate(self.sites, 1):
            print(f"{i}. {site}")
        
        while True:
            try:
                choice = input(f"Select site (1-{len(self.sites)}) or enter custom name: ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(self.sites):
                        return self.sites[idx]
                else:
                    # Custom site name
                    return choice
            except (ValueError, IndexError):
                print("Invalid selection, please try again")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 Universal Frappe Bench Setup")
        print("=" * 40)
        
        # Auto-detect configuration
        self.auto_detect_bench()
        
        # Confirm or override detection
        if input(f"\nUse detected bench directory '{self.bench_dir}'? (y/n): ").lower().strip() != 'y':
            self.bench_dir = input("Enter bench directory: ").strip()
            if not self.is_bench_directory(Path(self.bench_dir)):
                print("❌ Invalid bench directory")
                sys.exit(1)
        
        print(f"\n📁 Working with bench: {self.bench_dir}")
        
        # Select site
        site_name = self.select_site()
        print(f"🌐 Selected site: {site_name}")
        
        # Setup options
        print("\n⚙️ Configuration Options")
        print("-" * 30)
        
        # Developer mode
        if input("Enable developer mode? (y/n): ").lower().strip() == "y":
            self.enable_developer_mode()
        
        # Server scripts
        if input("Enable server scripts? (y/n): ").lower().strip() == "y":
            self.enable_server_scripts()
        
        # API credentials
        if input("Set Administrator API credentials? (y/n): ").lower().strip() == "y":
            api_key = input("Enter Administrator API key: ").strip()
            api_secret = getpass("Enter Administrator API secret: ")
            if api_key and api_secret:
                self.set_admin_api_keys(site_name, api_key, api_secret)
        
        # Update password
        if input("Update Administrator password? (y/n): ").lower().strip() == "y":
            self.update_admin_password(site_name)
        
        # CORS configuration
        self.set_cors()
        
        print("\n🎉 Setup completed!")
        print(f"📍 Bench: {self.bench_dir}")
        print(f"🌐 Site: {site_name}")

def main():
    try:
        setup = BenchSetup()
        setup.run_setup()
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

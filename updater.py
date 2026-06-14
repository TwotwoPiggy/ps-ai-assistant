import os
import sys
import subprocess
import shutil
import time
import requests
import zipfile

def get_project_dir():
    return os.path.dirname(os.path.abspath(__file__))

def update_via_git(project_dir):
    print("Detected Git repository. Pulling latest changes...")
    try:
        subprocess.run(["git", "pull"], cwd=project_dir, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git pull failed: {e}")
        return False

def update_via_zip(project_dir):
    print("Git repository not detected. Downloading latest source zip...")
    # NOTE: Since we do not have a specific github repo yet, this is a placeholder URL.
    # In a real scenario, this would be the actual repository release URL.
    zip_url = "https://github.com/placeholder/ps-ai-assistant/archive/refs/heads/main.zip"
    zip_path = os.path.join(project_dir, "update.zip")
    extract_dir = os.path.join(project_dir, "update_extracted")
    
    try:
        # Download
        response = requests.get(zip_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # Move files (excluding protected paths)
        # The github zip usually contains a single root folder e.g., ps-ai-assistant-main
        extracted_root = os.path.join(extract_dir, os.listdir(extract_dir)[0])
        
        protected_paths = {".venv", "backend/store", "node_modules"}
        
        for item in os.listdir(extracted_root):
            src_path = os.path.join(extracted_root, item)
            dst_path = os.path.join(project_dir, item)
            
            # Simple exclusion
            # Note: For complex nested exclusions like backend/store, 
            # we do a basic top-level check here for simplicity or handle specifically.
            if item in [p.split('/')[0] for p in protected_paths]:
                # If it's a directory that might contain protected sub-items, we need to merge carefully.
                # For this simple updater, we assume backend/store is protected.
                if item == "backend":
                    for subitem in os.listdir(src_path):
                        if subitem == "store":
                            continue
                        sub_src = os.path.join(src_path, subitem)
                        sub_dst = os.path.join(dst_path, subitem)
                        if os.path.isdir(sub_src):
                            if os.path.exists(sub_dst):
                                shutil.rmtree(sub_dst)
                            shutil.copytree(sub_src, sub_dst)
                        else:
                            shutil.copy2(sub_src, sub_dst)
                    continue
                elif item in protected_paths:
                    continue
            
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
                
    except Exception as e:
        print(f"Zip update failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
            
    return True

def install_dependencies(project_dir):
    print("Installing updated dependencies...")
    venv_python = os.path.join(project_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable
    
    try:
        subprocess.run([venv_python, "launcher.py", "--build-only"], cwd=project_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Dependency installation failed: {e}")

def restart_app(project_dir):
    print("Restarting application...")
    start_vbs = os.path.join(project_dir, "start_silent.vbs")
    if os.path.exists(start_vbs):
        os.startfile(start_vbs)
    else:
        print("start_silent.vbs not found. Please start the app manually.")

def main():
    print("--- PS AI Assistant Updater ---")
    project_dir = get_project_dir()
    
    # Wait for main process to exit
    time.sleep(2)
    
    if os.path.exists(os.path.join(project_dir, ".git")):
        success = update_via_git(project_dir)
    else:
        success = update_via_zip(project_dir)
        
    if success:
        install_dependencies(project_dir)
        print("Update finished successfully.")
    else:
        print("Update failed. Please check the logs.")
        
    restart_app(project_dir)

if __name__ == "__main__":
    main()

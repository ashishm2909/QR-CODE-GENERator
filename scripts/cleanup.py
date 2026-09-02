import os
import time

def cleanup_uploads(folder=None, max_age_days=1):
    """
    Remove files older than max_age_days from the specified folder.
    """
    if folder is None:
        # Resolve to standard upload path relative to project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(script_dir, '../backend/static/uploads')
    if not os.path.exists(folder):
        print(f"Folder {folder} does not exist.")
        return

    now = time.time()
    cutoff = now - (max_age_days * 86400)
    
    count = 0
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff:
                try:
                    os.remove(filepath)
                    count += 1
                except Exception as e:
                    print(f"Error removing {filename}: {e}")
                    
    print(f"Cleaned up {count} files from {folder}.")

if __name__ == "__main__":
    cleanup_uploads()

import shutil
import os

def update_cog(original_path: str, updated_path: str):
    if not os.path.isfile(updated_path):
        print(f"Updated file not found: {updated_path}")
        return False

    # Backup original file
    backup_path = original_path + ".bak"
    shutil.copy2(original_path, backup_path)
    print(f"Backed up {original_path} to {backup_path}")

    # Overwrite original file with updated
    shutil.copy2(updated_path, original_path)
    print(f"Updated {original_path} with {updated_path}")
    return True

def update_all_cogs(cogs_folder="cogs", updates_folder="updates"):
    updated_files = os.listdir(updates_folder)
    for update_file in updated_files:
        if not update_file.endswith(".py"):
            continue

        original_file = os.path.join(cogs_folder, update_file)
        updated_file = os.path.join(updates_folder, update_file)

        if os.path.isfile(original_file):
            try:
                update_cog(original_file, updated_file)
            except Exception as e:
                print(f"Failed to update {original_file}: {e}")
        else:
            print(f"Original cog file not found: {original_file}")

if __name__ == "__main__":
    update_all_cogs()

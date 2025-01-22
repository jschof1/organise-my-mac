import os
import shutil
from collections import Counter

def get_file_type(file_name, file_categories):
    """
    Determine the file type of a given file based on its extension.
    """
    file_extension = os.path.splitext(file_name)[1].lower()
    for category, extensions in file_categories.items():
        if file_extension in extensions:
            return category
    return "Others"

def determine_folder_category(folder_path, file_categories):
    """
    Determine the predominant category of files in a folder.
    """
    file_types = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_type = get_file_type(file, file_categories)
            file_types.append(file_type)
    if not file_types:
        return "Others"
    return Counter(file_types).most_common(1)[0][0]

def organise_folders_by_content(base_path):
    """
    Organise folders and files in the base directory by their predominant content.
    """
    # Define file type categories and their extensions
    file_categories = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
        "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
        "Videos": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"],
        "Archives": [".zip", ".rar", ".tar", ".gz", ".7z"],
        "Code": [
            ".py", ".js", ".html", ".css", ".java", ".c", ".cpp", ".php", ".rb",
            ".ts", ".jsx", ".tsx", ".astro", ".svelte", ".vue", ".json", ".yaml", ".yml"
        ],
        "Executables": [".exe", ".dmg", ".pkg"],
        "Others": []
    }

    # Create subfolders for each category
    category_paths = {}
    for category in file_categories.keys():
        category_path = os.path.join(base_path, category)
        os.makedirs(category_path, exist_ok=True)
        category_paths[category] = category_path

    # Process each item in the base directory
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)

        # Handle files
        if os.path.isfile(item_path):
            category = get_file_type(item, file_categories)
            dest_path = os.path.join(base_path, category, item)
            try:
                shutil.move(item_path, dest_path)
                print(f"Moved file: {item} -> {category}")
            except shutil.Error as e:
                print(f"Error moving file {item}: {e}")

        # Handle folders
        elif os.path.isdir(item_path) and item not in category_paths:
            category = determine_folder_category(item_path, file_categories)
            dest_path = os.path.join(base_path, category, item)
            try:
                shutil.move(item_path, dest_path)
                print(f"Moved folder: {item} -> {category}")
            except shutil.Error as e:
                print(f"Error moving folder {item}: {e}")

if __name__ == "__main__":
    # Prompt user to specify the base path
    base_path = input("Enter the folder path to organise: ").strip()

    # Expand the tilde (~) to the full home directory path
    base_path = os.path.expanduser(base_path)

    # Validate the input path
    if not os.path.isdir(base_path):
        print("Invalid path. Please make sure the folder exists.")
    else:
        organise_folders_by_content(base_path)
# Organise My Mac

Organise My Mac is a Python script that helps you organise files and folders on your Mac by categorising them into predefined folders (e.g., Images, Documents, Videos). It's a simple and efficient way to keep your directories neat and tidy.

## Features

- Automatically categorises files and folders into predefined categories.
- Handles both files and subfolders in the target directory.
- Supports flexible directory input, including paths with `~` (home directory).
- Prevents folders from being moved into themselves.

## File Categories

The script organises items into the following categories:

- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.svg`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.txt`, `.xls`, `.xlsx`, `.ppt`, `.pptx`
- **Audio**: `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`
- **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.flv`, `.wmv`
- **Archives**: `.zip`, `.rar`, `.tar`, `.gz`, `.7z`
- **Code**: `.py`, `.js`, `.html`, `.css`, `.java`, `.c`, `.cpp`, `.php`, `.rb`, `.ts`, `.jsx`, `.tsx`, `.astro`, `.svelte`, `.vue`, `.json`, `.yaml`, `.yml`
- **Executables**: `.exe`, `.dmg`, `.pkg`
- **Others**: Any files not matching the above categories.

## Installation

1. Download or clone the repository:
   ```bash
   git clone https://github.com/yourusername/organise-my-mac.git
```

2. Navigate to the project folder:
    
    ```bash
    cd organise-my-mac
    ```
    
3. Ensure Python is installed:
    
    ```bash
    python3 --version
    ```
    
    If Python is not installed, download it from [python.org](https://www.python.org/).
    

## Usage

1. Open a terminal and navigate to the `organise-my-mac` folder:
    
    ```bash
    cd /path/to/organise-my-mac
    ```
    
2. Run the script:
    
    ```bash
    python3 main.py
    ```
    
3. Enter the path of the folder you want to organise when prompted:
    
    * Absolute path: `/Users/jschof1/Downloads`
    * Relative path: `./Downloads`
    * Home directory shortcut: `~/Downloads`
4. The script will organise files and folders into subdirectories within the specified folder.
    

## Example

**Before Running**

```markdown
Downloads/
    file1.jpg
    file2.pdf
    file3.mp4
    Subfolder1/
    Subfolder2/
```

**After Running**

```markdown
Downloads/
    Images/
        file1.jpg
    Documents/
        file2.pdf
    Videos/
        file3.mp4
    Others/
        Subfolder1/
        Subfolder2/
```

## Customisation

To customise the file categories, open `main.py` and edit the `file_categories` dictionary. You can add, remove, or modify categories and their associated file extensions.

## Troubleshooting

**Invalid Path Error**  
If you see:

```arduino
Invalid path. Please make sure the folder exists.
```

Ensure the folder path you entered is correct and accessible.

**File/Folder Moving Errors**  
If you see errors like:

```bash
Error moving file/folder
```

Check:

* You have permission to modify the target directory.
* Files are not locked by another application.

## Contribution

Contributions are welcome! Feel free to fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
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

## Optional macOS resource guard

`resource_guard.py` is a separate Python 3 standard-library tool. It does not change
the organiser. Run it headlessly on a laptop or Mac Mini:

```sh
python3 resource_guard.py status --json
python3 resource_guard.py check
python3 resource_guard.py run -- make
python3 resource_guard.py monitor
python3 -B -m unittest -v test_resource_guard
```

Only commands explicitly passed to `run --` are gated. It refuses when the home
volume has less than 10 GiB available, one-minute load exceeds the logical CPU
count, measurements fail, or another guarded job holds the per-user `flock`.
Exactly 10 GiB and load equal to CPU count are allowed. `check` uses the same
gate and exits nonzero when unsuitable; `status` reports without starting work.
These are point-in-time checks, not reservations of disk or CPU capacity.

The lock stays held throughout the direct child command. The child inherits the
lock descriptor, including if the guard process exits unexpectedly. Daemonised
or detached work that closes inherited descriptors is outside this contract;
wrap foreground commands. `run` uses an argument list without shell evaluation,
adds 10 to niceness through macOS `nice`, and defaults only unset worker variables
to `CMAKE_BUILD_PARALLEL_LEVEL=2`, `UV_THREADPOOL_SIZE=2`, `MAKEFLAGS=-j2`.
Explicit environment settings win. The child exit code is retained (signals use
the conventional 128 + signal exit status).

Disk levels are critical below 10 GiB, low below 25 GiB, and healthy from 25 GiB.
Free capacity comes from available filesystem blocks on the actual home volume.
Jack Drive is available only at a real `/Volumes/Jack Drive` mount whose
`diskutil info -plist` reports VolumeUUID `77835823-7D54-386B-B6C2-2E65AB80C5B8`,
the expected mount point and no explicit Mounted=false. macOS may omit Mounted;
the actual mount check remains required. Missing or mismatched volumes report
unavailable with null free capacity; a fallback directory is never counted.

`monitor` performs one cheap pass and atomically replaces the bounded latest
`~/.local/state/mac-resource-guard/status.json`; it keeps no history. It attempts
a local macOS notification for low/critical disk or high load, at most once per
hour across all alerts, including failed attempts. Notification errors remain
visible in the saved status and subsequent `status` output. Headless checks do
not need a notification session. Repeated scheduling and launchd installation
are left to the operator; there is no `install` command. Monitor only reports
and alerts: it never deletes/moves user files or kills/suspends jobs or apps.
Both the state directory and lock paths resolve the current user's home at runtime.

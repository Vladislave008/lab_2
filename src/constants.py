import sys
from pathlib import Path
POSSIBLE_COMMANDS = ["ls", "cd", "cat", "cp", "mv", "rm", "zip", "unzip", "tar", "untar", "grep", "history", "undo", "pwd", "touch", "help"]
POSSIBLE_OPTIONS = {"ls": ["-l", "--help"],
                    "cd": ["--help"],
                    "cat": ["--help"],
                    "cp": ["-r", "--help"],
                    "mv": ["--help"],
                    "rm": ["-r", "--help"],
                    "zip": ["--help"],
                    "unzip": ["--help"],
                    "tar": ["--help"],
                    "untar": ["--help"],
                    "grep": ["-r", "-i", "--help"],
                    "history": ["-c", "--help"],
                    "undo": ["--help"],
                    "pwd": ["--help"],
                    "touch": ["--help"],
                    "help" : []}
DANGEROUS_PATHS = ["/", "\\","~", "/bin", "/sbin", "/usr", "/usr/bin", "/usr/sbin",
    "/etc", "/var", "/lib", "/lib64", "/sys", "/proc",
    "/dev", "/boot", "/root", "/opt",
     "C:\\", "D:\\", "E:\\", "F:\\",
    "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",
    "C:\\System32", "C:\\Users",
    sys.prefix, sys.exec_prefix,
    ".", ".."]

PROJECT_ROOT = Path(__file__).parent.parent

TRASH_PATH = PROJECT_ROOT / ".trash"
MOVE_BACKUP_PATH = PROJECT_ROOT / ".mv_backup"
COPY_BACKUP_PATH = PROJECT_ROOT / ".cp_backup"
LOGGER_PATH = PROJECT_ROOT / "shell.log"
HISTORY_PATH = PROJECT_ROOT / ".history"

HELP_MESSAGES = {
    "ls": "ls <path> - list directory contents\n  -l: detailed view with size, date, permissions",
    "cd": "cd <path> - change directory\n  ~ - home directory\n  .. - parent directory",
    "cat": "cat <file> - display file content",
    "cp": "cp <src> <dst> - copy files/directories\n  -r: recursive copy for directories",
    "mv": "mv <src> <dst> - move or rename files/directories",
    "rm": "rm <path> - remove files/directories\n  -r: recursive removal\n  requires confirmation",
    "pwd": "pwd - print working directory",
    "touch": "touch <file> - create empty file or update timestamp",
    "zip": "zip <source> <archive.zip> - create ZIP archive",
    "unzip": "unzip <archive.zip> - extract ZIP archive",
    "tar": "tar <source> <archive.tar> - create TAR archive",
    "untar": "untar <archive.tar> - extract TAR archive",
    "grep": "grep <pattern> <path> - search text in files\n  -r: recursive search\n  -i: ignore case",
    "history": "history <N> (optional) - show command history (last N commands)\n  -c: clear history",
    "undo": "undo - revert last cp/mv/rm/touch/cd operation",
}

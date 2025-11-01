import os
import shutil
from src.constants import POSSIBLE_COMMANDS, TRASH_PATH, MOVE_BACKUP_PATH, COPY_BACKUP_PATH, HISTORY_PATH
import logging
import shlex
from src.command_execute import CommandExecutor

class ShellSyntaxError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class Command:
    def __init__(self, command: str, data: dict):
        self.command = command
        self.data = data

class Shell:
    def __init__(self) -> None:
        self.setup_logging()
        self.drop_backup()
        self.executor = CommandExecutor(self.logger)

    def drop_backup(self) -> None:
        for path in [TRASH_PATH, COPY_BACKUP_PATH, MOVE_BACKUP_PATH]:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        shutil.rmtree(dir_path)

    def setup_logging(self) -> None:
        self.logger = logging.getLogger("shell")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s] %(message)s")
        file_handler = logging.FileHandler("shell.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def parse_line(self, line: str) -> None:
        with open(HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(f"{line}\n")
        self.logger.info(f"COMMAND: {line}")
        try:
            line_split = shlex.split(line)
        except ValueError as e:
            self.logger.info(f"ERROR: Invalid syntax - {e}")
            print(f"ShellSyntaxError: Invalid command syntax - {e}")
            return
        if len(line_split) == 0:
            self.logger.info("ERROR: No commands found")
            print("ShellSyntaxError: No commands found")
            return
        command = line_split[0]
        if command not in POSSIBLE_COMMANDS:
            self.logger.info(f"ERROR: Command does not exist: {command}")
            print(f"ShellSyntaxError: Command does not exist: {command}. Type 'help' to see command list")
            return
        args: list[str] = []
        options: list[str] = []
        options_done: bool = False # used to prevent getting options after args
        if len(line_split) > 1:
            for i in range(1, len(line_split)):
                elem = line_split[i]
                if not options_done and elem.startswith("-"):
                    if elem not in options: # skip option duplicates
                        options.append(elem)
                elif elem.startswith("-") and options_done:
                    self.logger.info("ERROR: Option after argument")
                    print(f"ShellSyntaxError: Option can't go after argument: {elem}")
                    return
                else:
                    options_done = True
                    if command == "grep":
                        if len(args) == 0:
                            args.append(elem)
                        else:
                            args.append(os.path.abspath(os.path.normpath(elem)))
                    elif command == "history":
                        args.append(elem)
                    else:
                        if elem.startswith('~'):
                            args.append(os.path.abspath(os.path.normpath(os.path.expanduser(elem))))
                        else:
                            args.append(os.path.abspath(os.path.normpath(elem)))
        match command:
            case "ls":
               self.executor.execute_ls(options, args)
            case "cd":
               self.executor.execute_cd(options, args)
            case "cat":
               self.executor.execute_cat(options, args)
            case "cp":
               self.executor.execute_cp(options, args, False)
            case "mv":
               self.executor.execute_mv(options, args, False)
            case "rm":
               self.executor.execute_rm(options, args, False)
            case "zip":
               self.executor.execute_zip(options, args)
            case "unzip":
               self.executor.execute_unzip(options, args)
            case "tar":
               self.executor.execute_tar(options, args)
            case "untar":
               self.executor.execute_untar(options, args)
            case "grep":
               self.executor.execute_grep(options, args)
            case "history":
               self.executor.execute_history(options, args)
            case "undo":
               self.executor.execute_undo(options, args)
            case "pwd":
               self.executor.execute_pwd(options, args)
            case "touch":
               self.executor.execute_touch(options, args)
            case "help":
               self.executor.execute_help(options, args)

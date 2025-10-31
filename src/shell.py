import os
import shutil
import stat
from src.constants import   POSSIBLE_COMMANDS, POSSIBLE_OPTIONS, DANGEROUS_PATHS, TRASH_PATH,\
                            MOVE_BACKUP_PATH, COPY_BACKUP_PATH, HISTORY_PATH, \
                            HELP_MESSAGES
import logging
import shlex
import zipfile
import tarfile
import re
import datetime
import uuid
import copy

class ShellSyntaxError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class Command:
    def __init__(self, command: str, data: dict):
        self.command = command
        self.data = data

class Shell:

    def __init__(self) -> None:
        self.command_stack: list[list[Command]] = []
        self.setup_logging()
        self.drop_backup()

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
        # print(command, options, args, sep = "\n")
        match command:
            case "ls":
                self.execute_ls(options, args)
            case "cd":
                self.execute_cd(options, args)
            case "cat":
                self.execute_cat(options, args)
            case "cp":
                self.execute_cp(options, args, False)
            case "mv":
                self.execute_mv(options, args, False)
            case "rm":
                self.execute_rm(options, args, False)
            case "zip":
                self.execute_zip(options, args)
            case "unzip":
                self.execute_unzip(options, args)
            case "tar":
                self.execute_tar(options, args)
            case "untar":
                self.execute_untar(options, args)
            case "grep":
                self.execute_grep(options, args)
            case "history":
                self.execute_history(options, args)
            case "undo":
                self.execute_undo(options, args)
            case "pwd":
                self.execute_pwd(options, args)
            case "touch":
                self.execute_touch(options, args)
            case "help":
                self.execute_help(options, args)
        #print("COMMAND STACK: ", [[(elem2.command, elem2.data) for elem2 in elem] for elem in self.command_stack])

    def execute_help(self, options: list[str], args: list[str]) -> None:
        for elem in HELP_MESSAGES.values():
            print(elem)

    def execute_pwd(self, options: list[str], args: list[str]) -> None:
        ''' Prints current working directory
            Args:
                options (list[str]): options for command
                args (list[str]): arguments for command
            Might throw:
                ShellSyntaxError: syntax error appeared in command line
                Exception: unexpected exeption '''
        try:
            if "--help" in options:
                print(HELP_MESSAGES["pwd"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command pwd doesn't take options")
            if len(args) != 0:
                raise ShellSyntaxError("Command pwd doesn't take arguments")
            print(os.path.abspath(os.curdir))
            self.logger.info("SUCCESS: pwd completed")
        except ShellSyntaxError as e:
            print(f"ShellSyntaxError: {e}")
        except Exception:
            print("Unexpected exception appeared")

    def execute_touch(self, options: list[str], args: list[str]) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["touch"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command touch doesn't take options")
            if len(args) < 1:
                raise ShellSyntaxError("Command touch requires at least 1 argument: <path>")
            stack_unit = []
            for path in args:
                try:
                    parent_dir = os.path.dirname(path)
                    if parent_dir and not os.path.exists(parent_dir):
                        os.makedirs(parent_dir, exist_ok=True)
                    if os.path.exists(path):
                        os.utime(path, None)
                    else:
                        for prohibited in r'[<>:"/\|?*\]':
                            if prohibited in os.path.basename(path):
                                raise ShellSyntaxError(f"Character {prohibited} can't be used in filenames: {os.path.basename(path)}")
                        open(path, "w").close()
                        command_dict = {}
                        command_dict["target_path"] = path
                        stack_unit.append(Command("touch", command_dict))
                    self.logger.info(f"SUCCESS: touch {path} completed")
                except ShellSyntaxError as e:
                    self.logger.info("ERROR: touch failed - ShellSyntaxError")
                    print(f"ShellSyntaxError: {e}")
                except Exception:
                    self.logger.info("ERROR: touch failed - Unexpected exception")
                    print("Unexpected exception appeared")
            self.command_stack.append(stack_unit)
        except ShellSyntaxError as e:
            self.logger.info("ERROR: touch failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: touch failed - Unexpected exception")
            print("Unexpected exception appeared")

    @staticmethod
    def mode_to_str(perm: int) -> str:
        ''' Gets bash-styled permission values from int-typed permission values by using "bitwise and" operator
            Args:
                perm (int): int-typed permission value
            Returns:
                str: bash-styled permission value '''
        file_type = "d" if stat.S_ISDIR(perm) else "-"
        res = "".join([
            "r" if perm & stat.S_IRUSR else "-",
            "w" if perm & stat.S_IWUSR else "-",
            "x" if perm & stat.S_IXUSR else "-",
            "r" if perm & stat.S_IRGRP else "-",
            "w" if perm & stat.S_IWGRP else "-",
            "x" if perm & stat.S_IXGRP else "-",
            "r" if perm & stat.S_IROTH else "-",
            "w" if perm & stat.S_IWOTH else "-",
            "x" if perm & stat.S_IXOTH else "-"])
        return file_type + res

    def execute_ls(self, options: list[str], args: list[str]) -> None:
        ''' Executes ls command (shows content of the current working directory)
            Args:
                options (list[str]): options for command
                args (list[str]): arguments for command
            Might throw:
                FileNotFoundError: given directory from args doesn't exist
                NotADirectoryError: file is mentioned as an argument
                PermissionError: Not enought rights to execute command
                ShellSyntaxError: syntax error appeared in command line
                Exception: unexpected exeption '''
        try:
            if "--help" in options:
                print(HELP_MESSAGES["ls"])
                return
            for option in options:
                if option not in POSSIBLE_OPTIONS["ls"]:
                    raise ShellSyntaxError(f"Command ls doesn't take such option: {option}")
            if len(args) == 0:
                dir_name = "."
            elif len(args) == 1:
                dir_name = args[0]
            else:
                raise ShellSyntaxError("Command ls requires 1 argument: <path>")
            if "-l" in options:
                for file_name in os.listdir(dir_name):
                    full_file_name = os.path.join(dir_name, file_name)
                    file_stat = os.stat(full_file_name)
                    if len(file_name) > 30:
                        file_name = file_name[:30] + "..."
                    line = f"{file_name:<33} {file_stat.st_size:>15} {(datetime.datetime.fromtimestamp(file_stat.st_mtime)).strftime("%Y-%m-%d %H:%M"):>16} {self.mode_to_str((file_stat.st_mode)):>10}"
                    print(line)
            else:
                res = os.listdir(dir_name)
                print("\n".join(res))
            self.logger.info(f"SUCCESS: ls {dir_name} completed")
        except FileNotFoundError:
            self.logger.info("ERROR: ls failed - FileNotFoundError")
            print(f"FileNotFoundError: Directory {dir_name} doesn't exist")
        except NotADirectoryError:
            self.logger.info("ERROR: ls failed - NotADirectoryError")
            print("NotADirectoryError: command ls doesn't take file as an argument")
        except PermissionError:
            self.logger.info("ERROR: ls failed - PermissionError")
            print("PermissionError: Not enough rights to execute command")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: ls failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: ls failed - Unexpected exception")
            print("Unexpected exception appeared")

    def execute_cd(self, options: list[str], args: list[str]) -> None:
        ''' Executes cd command (changes current working directory)
            Args:
                options (list[str]): options for command
                args (list[str]): arguments for command
            Might throw:
                FileNotFoundError: given directory from args doesn't exist
                PermissionError: Not enought rights to execute command
                NotADirectoryError: file is mentioned as an argument
                ShellSyntaxError: syntax error appeared in command line
                Exception: unexpected exeption '''
        try:
            if "--help" in options:
                print(HELP_MESSAGES["cd"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command cd doesn't take options")
            if len(args) != 1:
                raise ShellSyntaxError("Command cd requires 1 argument: <path>")
            self.command_stack.append([Command("cd", {"source_path": os.getcwd(), "target_path": args[0]})])
            os.chdir(args[0])
            self.logger.info(f"SUCCESS: cd {args[0]} completed")
        except NotADirectoryError:
            self.logger.info("ERROR: cd failed - NotADirectoryError")
            print("NotADirectoryError: command cd doesn't take file as an argument")
        except FileNotFoundError:
            self.logger.info("ERROR: cd failed - FileNotFoundError")
            print(f"FileNotFoundError: Directory {args[0]} doesn't exist")
        except PermissionError:
            self.logger.info("ERROR: cd failed - PermissionError")
            print("PermissionError: Not enough rights to execute command")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: cd failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: cd failed - Unexpected exception")
            print("Unexpected exception appeared")

    def execute_cat(self, options: list[str], args: list[str]) -> None:
        ''' Executes cat command (shows content of the given file line by line)
            Args:
                options (list[str]): options for command
                args (list[str]): arguments for command
            Might throw:
                IsADirectoryError: directory is mentioned as an argument
                FileNotFoundError: given directory from args doesn't exist
                PermissionError: Not enought rights to execute command
                ShellSyntaxError: syntax error appeared in command line
                UnicodeDecodeError: unable to read file because of encoding type
                Exception: unexpected exeption '''
        try:
            if "--help" in options:
                print(HELP_MESSAGES["cat"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command cat doesn't take options")
            elif len(args) != 1:
                raise ShellSyntaxError("Command cat requires 1 argument: <file>")
            if not os.path.exists(args[0]):
                raise FileNotFoundError(f"File {args[0]} doesn't exist")
            if os.path.isdir(args[0]):
                raise IsADirectoryError("Command cat takes only files as arguments")
            with open(args[0], "r", encoding="utf-8") as f:
                res = [line.rstrip('\n') for line in f]
            print("\n".join(res))
            self.logger.info(f"SUCCESS: cat {args[0]} completed")
        except IsADirectoryError:
            self.logger.info("ERROR: cat failed - IsADirectoryError")
            print("IsADirectoryError: Command cat takes only files as arguments")
        except FileNotFoundError:
            self.logger.info("ERROR: cat failed - FileNotFoundError")
            print(f"FileNotFoundError: File {args[0]} doesn't exist")
        except PermissionError:
            self.logger.info("ERROR: cat failed - PermissionError")
            print("PermissionError: Not enough rights to execute command")
        except UnicodeDecodeError:
            self.logger.info("ERROR: cat failed - UnicodeDecodeError")
            print("UnicodeDecodeError: Unable to read file because of encoding type")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: cat failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: cat failed - Unexpected exception")
            print("Unexpected exception appeared")

    def execute_cp(self, options: list[str], args: list[str], is_undo: bool) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["cp"])
                return
            for option in options:
                    if option not in POSSIBLE_OPTIONS["cp"]:
                        raise ShellSyntaxError(f"Command cp doesn't take such option: {option}")
            if len(args) < 2:
                raise ShellSyntaxError("Command cp requires at least 2 arguments: <source path> <target path>")
            dst = args[-1]
            stack_unit = []
            for i in range(len(args)-1):
                try:
                    src = args[i]
                    if self.is_dangerous_path(src):
                            raise ShellSyntaxError(f"Can't execute mv - this argument might lead to crash: {src}")
                    if not is_undo:
                        if not os.path.exists(src):
                            raise FileNotFoundError(src)
                        if "-r" in options:
                            if not os.path.isdir(src):
                                raise NotADirectoryError("Source must be a directory for cp -r")
                            if os.path.isdir(dst):
                                final_dst = os.path.join(dst, os.path.basename(src))
                            else:
                                final_dst = dst
                            parent_dir = os.path.dirname(final_dst)
                            if parent_dir and not os.path.exists(parent_dir):
                                os.makedirs(parent_dir, exist_ok=True)
                            target_path = shutil.copytree(src, final_dst, dirs_exist_ok=True) # с перезаписью существующих
                            stack_unit.append(Command("cp", {"is_recursive": True, "target_path": target_path}))
                        else:
                            if not os.path.isfile(src):
                                raise IsADirectoryError("Source must be a file for cp (use -r for directories)")
                            if os.path.isdir(dst):
                                final_dst = os.path.join(dst, os.path.basename(src))
                            else:
                                final_dst = dst
                            parent_dir = os.path.dirname(final_dst)
                            if parent_dir and not os.path.exists(parent_dir):
                                os.makedirs(parent_dir, exist_ok=True)
                            command_dict = {}
                            backup_id = str(uuid.uuid4())[:8]
                            if os.path.isfile(src) and os.path.isfile(dst):
                                self.execute_cp([],[dst,  os.path.join(COPY_BACKUP_PATH, backup_id + os.path.basename(dst))], True)
                                command_dict["backup_path"] = os.path.join(COPY_BACKUP_PATH, backup_id + os.path.basename(dst))
                            else:
                                command_dict["backup_path"] = None # type: ignore[assignment]
                            target_path = shutil.copy2(src, final_dst)
                            command_dict["target_path"] = target_path
                            command_dict["source_path"] = src
                            command_dict["is_recursive"] = False # type: ignore[assignment]
                            stack_unit.append(Command("cp", command_dict))
                        self.logger.info(f"SUCCESS: cp {src} to {dst} completed")
                    elif is_undo:
                        if "-r" in options:
                            if not os.path.isdir(src):
                                raise NotADirectoryError("Source must be a directory for cp -r")
                            if os.path.isdir(dst):
                                final_dst = os.path.join(dst, os.path.basename(src))
                            else:
                                final_dst = dst
                            parent_dir = os.path.dirname(final_dst)
                            if parent_dir and not os.path.exists(parent_dir):
                                os.makedirs(parent_dir, exist_ok=True)
                            target_path = shutil.copytree(src, final_dst, dirs_exist_ok=True) # с перезаписью существующих
                        else:
                            if not os.path.isfile(src):
                                raise IsADirectoryError("Source must be a file for cp (use -r for directories)")
                            if os.path.isdir(dst):
                                final_dst = os.path.join(dst, os.path.basename(src))
                            else:
                                final_dst = dst
                            parent_dir = os.path.dirname(final_dst)
                            if parent_dir and not os.path.exists(parent_dir):
                                os.makedirs(parent_dir, exist_ok=True)
                            target_path = shutil.copy2(src, final_dst)
                        self.logger.info(f"SUCCESS: cp (for undo) {src} to {dst} completed")
                except FileNotFoundError as e:
                    self.logger.info("ERROR: cp failed - FieNotFoundError")
                    print(f"FileNotFoundError: Given file or directory doesn't exist: {e}")
                except IsADirectoryError:
                    self.logger.info("ERROR: cp failed - IsADirectoryError")
                    print("IsADirectoryError: File was expected as an argument but a directory was given")
                except NotADirectoryError:
                    self.logger.info("ERROR: cp failed - NotADirectoryError")
                    print("NotADirectoryError: Directory was expected as an argument but something else was given (-r might be the reason)")
                except PermissionError:
                    self.logger.info("ERROR: cp failed - PermissionError")
                    print("PermissionError: Not enough rights to execute command")
                except ShellSyntaxError as e:
                    self.logger.info("ERROR: cp failed - ShellSyntaxError")
                    print(f"ShellSyntaxError: {e}")
                except Exception:
                    self.logger.info("ERROR: cp failed - Unexpected exception")
                    print("Unexpected exception appeared")
            if not is_undo and stack_unit != []:
                self.command_stack.append(stack_unit)
        except ShellSyntaxError as e:
            self.logger.info("ERROR: cp failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")

    def execute_mv(self, options: list[str], args: list[str], is_undo: bool) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["mv"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command mv doesn't take options")
            if len(args) < 2:
                raise ShellSyntaxError("Command mv requires at least 2 arguments: <source path> <target path>")
            dst = args[-1]
            stack_unit = []
            for i in range(len(args)-1):
                try:
                    src = args[i]
                    if self.is_dangerous_path(src):
                            raise ShellSyntaxError(f"Can't execute mv - this argument might lead to crash: {src}")
                    if not is_undo:
                        if not os.path.exists(src):
                            raise FileNotFoundError(src)
                        if os.path.isdir(dst):
                            final_dst = os.path.join(dst, os.path.basename(src))
                        else:
                            final_dst = dst
                        parent_dir = os.path.dirname(final_dst)
                        if parent_dir and not os.path.exists(parent_dir):
                            os.makedirs(parent_dir, exist_ok=True)
                        command_dict = {}
                        backup_id = str(uuid.uuid4())[:8]
                        if os.path.isfile(src) and os.path.isfile(dst):
                            self.execute_cp([],[dst, os.path.join(MOVE_BACKUP_PATH, backup_id + os.path.basename(dst))], True)
                            command_dict["backup_path"] = os.path.join(MOVE_BACKUP_PATH, backup_id + os.path.basename(dst))
                        else:
                            command_dict["backup_path"] = None # type: ignore[assignment]
                        target_path = shutil.move(src, final_dst)
                        command_dict["target_path"] = target_path
                        command_dict["source_path"] = src
                        stack_unit.append(Command("mv", command_dict))
                        self.logger.info(f"SUCCESS: mv {src} to {dst} completed")
                    elif is_undo:
                        if not os.path.exists(src):
                            raise FileNotFoundError(src)
                        if os.path.isdir(dst):
                            final_dst = os.path.join(dst, os.path.basename(src))
                        else:
                            final_dst = dst
                        parent_dir = os.path.dirname(final_dst)
                        if parent_dir and not os.path.exists(parent_dir):
                            os.makedirs(parent_dir, exist_ok=True)
                        shutil.move(src, final_dst)
                        self.logger.info(f"SUCCESS: mv (for undo) {src} to {dst} completed")
                except FileNotFoundError as e:
                    self.logger.info("ERROR: mv failed - FileNotFoundError")
                    print(f"FileNotFoundError: Given file or directory doesn't exist: {e}")
                except IsADirectoryError:
                    self.logger.info("ERROR: mv failed - IsADirectoryError")
                    print("IsADirectoryError: File was expected as an argument but a directory was given")
                except NotADirectoryError:
                    self.logger.info("ERROR: mv failed - NotADirectoryError")
                    print("NotADirectoryError: Directory was expected as an argument but something else was given")
                except PermissionError:
                    self.logger.info("ERROR: mv failed - PermissionError")
                    print("PermissionError: Not enough rights to execute command")
                except ShellSyntaxError as e:
                    self.logger.info("ERROR: mv failed - ShellSyntaxError")
                    print(f"ShellSyntaxError: {e}")
                except Exception:
                    self.logger.info("ERROR: mv failed - Unexpected exception")
                    print("Unexpected exception appeared")
            if not is_undo and stack_unit != []:
                self.command_stack.append(stack_unit)
        except ShellSyntaxError as e:
            self.logger.info("ERROR: mv failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")

    @staticmethod
    def confirm_deletion(path, is_recursive=False) -> bool:
        if is_recursive:
            message = f"Are you sure to recursively remove {path}?"
        else:
            message = f"Are you sure to remove {path}?"
        while True:
            check = input(f"{message} (y/n): ").lower().strip()
            if check in ["y", "yes"]:
                return True
            elif check in ["n", "no"]:
                return False
            print("Please enter 'y' or 'n'")

    @staticmethod
    def is_dangerous_path(path: str) -> bool:
        abs_path = os.path.abspath(os.path.expanduser(path))
        for dangerous in DANGEROUS_PATHS:
            dangerous_abs = os.path.abspath(os.path.expanduser(dangerous))
            if abs_path == dangerous_abs:
                return True
        if (os.getcwd()).startswith(abs_path):
            return True
        backup_dirs = [".cp_backup", ".trash", ".mv_backup"]
        if os.path.basename(abs_path) in backup_dirs:
            return True
        return False

    def execute_rm(self, options: list[str], args: list[str], is_undo: bool) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["rm"])
                return
            if len(args) < 1:
                    raise ShellSyntaxError("Command rm requires at least 1 argument: <path>")
            stack_unit = []
            for path in args:
                try:
                    if not is_undo:
                        if self.is_dangerous_path(path):
                            raise ShellSyntaxError(f"Can't execute rm - this argument might lead to crash: {path}")
                        if not os.path.exists(path):
                            raise FileNotFoundError(path)
                        trash_id = str(uuid.uuid4())[:8]
                        if "-r" in options:
                            if os.path.isdir(path):
                                if self.confirm_deletion(path, True):
                                    self.execute_cp(["-r"],[path,  os.path.join(TRASH_PATH, trash_id + os.path.basename(path))], True)
                                    shutil.rmtree(path)
                                    stack_unit.append(Command("rm", {"source_path": path, "trash_path": os.path.join(TRASH_PATH, trash_id + os.path.basename(path))}))
                            else:
                                if self.confirm_deletion(path, True):
                                    self.execute_cp([],[path,  os.path.join(TRASH_PATH, trash_id + os.path.basename(path))], True)
                                    os.remove(path)
                                    stack_unit.append(Command("rm", {"source_path": path, "trash_path": os.path.join(TRASH_PATH, trash_id + os.path.basename(path))}))
                        else:
                            if os.path.isdir(path):
                                if not os.listdir(path):
                                    if self.confirm_deletion(path, False):
                                        self.execute_cp(["-r"],[path,  os.path.join(TRASH_PATH, trash_id + os.path.basename(path))], True)
                                        os.rmdir(path)
                                        stack_unit.append(Command("rm", {"source_path": path, "trash_path": os.path.join(TRASH_PATH, trash_id + os.path.basename(path))}))
                                else:
                                    raise ShellSyntaxError(f"Can't delete unempty folder without -r option: {path}")
                            else:
                                if self.confirm_deletion(path, False):
                                    self.execute_cp([],[path,  os.path.join(TRASH_PATH, trash_id + os.path.basename(path))], True)
                                    os.remove(path)
                                    stack_unit.append(Command("rm", {"source_path": path, "trash_path": os.path.join(TRASH_PATH, trash_id + os.path.basename(path))}))
                        self.logger.info(f"SUCCESS: rm {path} completed")
                    elif is_undo:
                        if self.is_dangerous_path(path):
                            raise ShellSyntaxError(f"Can't execute rm - this argument might lead to crash: {path}")
                        if not os.path.exists(path):
                            raise FileNotFoundError(path)
                        if "-r" in options:
                            if os.path.isdir(path):
                                shutil.rmtree(path)
                            else:
                                os.remove(path)
                        else:
                            if os.path.isdir(path):
                                if not os.listdir(path):
                                    os.rmdir(path)
                                else:
                                    raise ShellSyntaxError(f"Can't delete unempty folder without -r option: {path}")
                            else:
                                os.remove(path)
                        self.logger.info(f"SUCCESS: rm (for undo) {path} completed")
                except FileNotFoundError:
                    self.logger.info("ERROR: rm failed - FileNotFoundError")
                    print(f"FileNotFoundError: Given file or directory doesn't exist: {path}")
                except PermissionError:
                    self.logger.info("ERROR: rm failed - PermissionError")
                    print("PermissionError: Not enough rights to execute command")
                except ShellSyntaxError as e:
                    self.logger.info("ERROR: rm failed - ShellSyntaxError")
                    print(f"ShellSyntaxError: {e}")
                except Exception:
                    self.logger.info("ERROR: rm failed - Unexpected exception")
                    print("Unexpected exception appeared")
            if not is_undo and stack_unit != []:
                self.command_stack.append(stack_unit)
        except ShellSyntaxError as e:
            self.logger.info("ERROR: rm failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")

    def execute_zip(self, options: list[str], args: list[str]) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["zip"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command zip doesn't take options")
            if len(args) != 2:
                raise ShellSyntaxError("Command zip requires 2 arguments: <source_folder> <archive>")
            path, archive = args[0], args[1]
            if not archive.endswith('.zip'):
                archive += '.zip'
            if not os.path.exists(path):
                raise FileNotFoundError(f"Source not found: {path}")
            with zipfile.ZipFile(archive, 'w') as zip:
                if os.path.isfile(path):
                    zip.write(path, os.path.basename(path))
                else:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            archname = os.path.relpath(file_path, os.path.dirname(path))
                            zip.write(file_path, archname)
            self.logger.info(f"SUCCESS: zip {path} to {archive} completed")
        except FileNotFoundError:
            self.logger.info("ERROR: zip failed - FileNotFoundError")
            print("FileNotFoundError: Given file or directory doesn't exist")
        except IsADirectoryError:
            self.logger.info("ERROR: zip failed - IsADirectoryError")
            print("IsADirectoryError: File was expected as an argument but a directory was given")
        except NotADirectoryError:
            self.logger.info("ERROR: zip failed - NotADirectoryError")
            print("NotADirectoryError: Directory was expected as an argument but something else was given")
        except PermissionError:
            self.logger.info("ERROR: zip failed - PermissionError")
            print("PermissionError: Not enough rights to execute command")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: zip failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: zip failed - Unexpected exception")
            print("Unexpected exception appeared")

    def execute_unzip(self, options: list[str], args: list[str]) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["unzip"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command unzip doesn't take options")
            if len(args) != 1:
                raise ShellSyntaxError("Command unzip requires 1 argument: <archive>")
            archive = args[0]
            if not archive.endswith('.zip'):
                archive += '.zip'
            if not os.path.exists(archive):
                raise FileNotFoundError(f"Archive not found: {archive}")
            if not zipfile.is_zipfile(archive):
                raise ShellSyntaxError(f"Not a ZIP archive: {archive}")
            with zipfile.ZipFile(archive, 'r') as zip:
                zip.extractall()
            self.logger.info(f"SUCCESS: unzip {archive} completed")
        except FileNotFoundError:
            self.logger.info("ERROR: unzip failed - FileNotFoundError")
            print("FileNotFoundError: Given file or directory doesn't exist")
        except IsADirectoryError:
            self.logger.info("ERROR: unzip failed - IsADirectoryError")
            print("IsADirectoryError: File was expected as an argument but a directory was given")
        except NotADirectoryError:
            self.logger.info("ERROR: unzip failed - NotADirectoryError")
            print("NotADirectoryError: Directory was expected as an argument but something else was given")
        except PermissionError:
            self.logger.info("ERROR: unzip failed - PermissionError")
            print("PermissionError: Not enough rights to execute command")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: unzip failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: unzip failed - Unexpected exception")
            print("Unexpected exception appeared")

    def execute_tar(self, options: list[str], args: list[str]) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["tar"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command tar doesn't take options")
            if len(args) != 2:
                raise ShellSyntaxError("Command tar requires 2 arguments: <source_folder> <archive>")
            path, archive = args[0], args[1]
            if not archive.endswith('.tar'):
                archive += '.tar'
            if not os.path.exists(path):
                raise FileNotFoundError(f"Source not found: {path}")
            with tarfile.TarFile(archive, 'w') as tar:
                if os.path.isfile(path):
                    tar.add(path, os.path.basename(path))
                else:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            archname = os.path.relpath(file_path, os.path.dirname(path))
                            tar.add(file_path, archname)
            self.logger.info(f"SUCCESS: tar {path} to {archive} completed")
        except FileNotFoundError:
            self.logger.info("ERROR: tar failed - FileNotFoundError")
            print("FileNotFoundError: Given file or directory doesn't exist")
        except IsADirectoryError:
            self.logger.info("ERROR: tar failed - IsADirectoryError")
            print("IsADirectoryError: File was expected as an argument but a directory was given")
        except NotADirectoryError:
            self.logger.info("ERROR: tar failed - NotADirectoryError")
            print("NotADirectoryError: Directory was expected as an argument but something else was given")
        except PermissionError:
            self.logger.info("ERROR: tar failed - PermissionError")
            print("PermissionError: Not enough rights to execute command")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: tar failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: tar failed - Unexpected exception")
            print("Unexpected exception appeared")

    def execute_untar(self, options: list[str], args: list[str]) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["untar"])
                return
            if len(args) != 1:
                raise ShellSyntaxError("Command untar requires 1 argument: <archive>")
            archive = args[0]
            if not archive.endswith('.tar'):
                        archive += '.tar'
            if not os.path.exists(archive):
                raise FileNotFoundError(f"Archive not found: {archive}")
            if not tarfile.is_tarfile(archive):
                raise ShellSyntaxError(f"Not a TAR archive: {archive}")
            with tarfile.open(archive, "r:*") as tar:
                tar.extractall()
            self.logger.info(f"SUCCESS: untar {archive} completed")
        except FileNotFoundError:
            self.logger.info("ERROR: untar failed - FileNotFoundError")
            print("FileNotFoundError: Given file or directory doesn't exist")
        except IsADirectoryError:
            self.logger.info("ERROR: untar failed - IsADirectoryError")
            print("IsADirectoryError: File was expected as an argument but a directory was given")
        except NotADirectoryError:
            self.logger.info("ERROR: untar failed - NotADirectoryError")
            print("NotADirectoryError: Directory was expected as an argument but something else was given")
        except PermissionError:
            self.logger.info("ERROR: untar failed - PermissionError")
            print("PermissionError: Not enough rights to execute command")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: untar failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: untar failed - Unexpected exception")
            print("Unexpected exception appeared")

    @staticmethod
    def find_re_matches_in_file(file_path: str, pattern: str, flags: int) -> list[tuple[int, str]]:
        """Ищет совпадения регулярки в файле"""
        matches: list[tuple[int, str]] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.rstrip('\n')
                    if re.search(pattern, line, flags):
                        matches.append((line_num, line))
        except UnicodeDecodeError:
            return []
        return matches

    def execute_grep(self, options: list[str], args: list[str]) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["grep"])
                return
            for option in options:
                if option not in POSSIBLE_OPTIONS["grep"]:
                    raise ShellSyntaxError(f"Command grep doesn't take such option: {option}")
            if len(args) != 2:
                raise ShellSyntaxError("Command grep takes two arguments: <pattern> <path>")
            pattern, path = args[0], args[1]
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            flags = re.IGNORECASE if "-i" in options else 0
            if "-r" in options:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        matches = self.find_re_matches_in_file(file_path, pattern, flags)
                        for line_num, line in matches:
                            print(f"File: {file_path}:{line_num}\nMatch: {line}\n")
            else:
                if os.path.isfile(path):
                    matches = self.find_re_matches_in_file(path, pattern, flags)
                    for line_num, line in matches:
                        print(f"File: {path}:{line_num}\nMatch: {line}\n")
                elif os.path.isdir(path):
                    for file in os.listdir(path):
                        file_path = os.path.join(path, file)
                        if os.path.isfile(file_path):
                            matches = self.find_re_matches_in_file(file_path, pattern, flags)
                            for line_num, line in matches:
                                print(f"File: {file_path}:{line_num}\nMatch: {line}\n")
                self.logger.info(f"SUCCESS: grep {pattern} {path} completed")
        except UnicodeDecodeError:
            self.logger.info("ERROR: grep failed - UnicodeDecodeError")
            print("UnicodeDecodeError: Unable to read file because of encoding type")
        except PermissionError:
            self.logger.info("ERROR: grep failed - PermissionError")
            print("PermissionError: Not enough rights to execute command")
        except FileNotFoundError as e:
            self.logger.info(f"ERROR: grep {pattern} {path} failed - FileNotFoundError")
            print(f"FileNotFoundError: Given file or directory doesn't exist: {e}")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: grep failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception as e:
            self.logger.info("ERROR: grep failed - Unexpected exception")
            print("Unexpected exception appeared", e)

    def execute_history(self, options: list[str], args: list[str]) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["history"])
                return
            for option in options:
                if option not in POSSIBLE_OPTIONS["history"]:
                    raise ShellSyntaxError(f"Command history doesn't take such option: {option}")
            if len(args) == 1:
                n_str: str  = args[0]
                try:
                    if n_str.isdigit():
                        n: int = int(n_str)
                    else:
                        raise Exception
                except Exception:
                    raise ShellSyntaxError("History <N> argument must be a positive integer")
            elif len(args) == 0:
                n = -1
            else :
                raise ShellSyntaxError("Command history takes 1 argument: <N>")
            if "-c" in options:
                with open(HISTORY_PATH, "w") as f:
                    f.write('')
            else:
                with open(HISTORY_PATH, "r") as f:
                    lines = [f"{i+1} {line.strip()}" for i, line in enumerate(f) if line.strip()]
                    if n >= len(lines) or n == -1:
                        print('\n'.join(lines))
                    else:
                        for i in range(len(lines)-n,len(lines)):
                            print(lines[i])
            self.logger.info("SUCCESS: history completed")
        except ShellSyntaxError as e:
            self.logger.info("ERROR: history failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: history failed - Unexpected exception")
            print("Unexpected exception appeared")

    @staticmethod
    def remove_last_line(filename) -> None:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if lines:
            for i in range(len(lines)-1, -1, -1):
                if lines[i].strip():
                    lines.pop(i)
                    break
            with open(filename, "w", encoding="utf-8") as f:
                f.writelines(lines)

    def execute_undo(self, options: list[str], args: list[str]) -> None:
        try:
            if "--help" in options:
                print(HELP_MESSAGES["undo"])
                return
            if len(options) != 0:
                raise ShellSyntaxError("Command undo doesn't take options")
            if len(args) != 0:
                raise ShellSyntaxError("Command undo doesn't take args")
            if len(self.command_stack) == 0:
                raise ShellSyntaxError("Command stack is empty (nothing to undo)")
            stack_unit = self.command_stack[-1]
            stack_unit_copy = copy.deepcopy(stack_unit)
            for i in range(len(stack_unit_copy)):
                try:
                    command = stack_unit_copy[i].command
                    data = stack_unit_copy[i].data
                    if command == "rm":
                        trash_path = data["trash_path"]
                        source_path =  data["source_path"]
                        if not os.path.exists(trash_path):
                            raise ShellSyntaxError("Unable to perform undo: some paths were deleted or moved by user")
                        self.execute_mv([], [trash_path, source_path], True)
                        print(f"Undo: {source_path} has been restored")
                    elif command == "cp":
                        if data["is_recursive"]:
                            target_path = data["target_path"]
                            if target_path is not None and not os.path.exists(target_path):
                                raise ShellSyntaxError("Unable to perform undo: some paths were deleted or moved by user")
                            self.execute_rm(["-r"], [target_path], True)
                        elif not data["is_recursive"]:
                            target_path = data["target_path"]
                            backup_path =  data["backup_path"]
                            for path in [target_path, backup_path]:
                                if path is not None and not os.path.exists(path):
                                    raise ShellSyntaxError("Unable to perform undo: some paths were deleted or moved by user")
                            if backup_path is None:
                                self.execute_rm([], [target_path], True)
                            elif backup_path is not None:
                                self.execute_mv([], [backup_path, target_path], True)
                        print(f"Undo: {target_path} has been deleted")
                    elif command == "mv":
                        source_path =  data["source_path"]
                        target_path = data["target_path"]
                        backup_path =  data["backup_path"]
                        for path in [target_path, backup_path]:
                            if path is not None and not os.path.exists(path):
                                raise ShellSyntaxError("Unable to perform undo: some paths were deleted or moved by user")
                        if backup_path is None:
                            self.execute_mv([], [target_path, source_path], True)
                        elif backup_path is not None:
                            self.execute_mv([], [target_path, source_path], True)
                            self.execute_mv([], [backup_path, target_path], True)
                        print(f"Undo: {target_path} has been moved back to {source_path}")
                    elif command == "touch":
                        target_path = data["target_path"]
                        if not os.path.exists(target_path):
                            raise ShellSyntaxError("Unable to perform undo: some paths were deleted or moved by user")
                        else:
                            self.execute_rm([], [target_path], True)
                        print(f"Undo: {target_path} has been deleted")
                    elif command == "cd":
                        source_path =  data["source_path"]
                        target_path = data["target_path"]
                        if not os.path.exists(source_path):
                            raise ShellSyntaxError("Unable to perform undo: some paths were deleted or moved by user")
                        os.chdir(source_path)
                        print(f"Undo: cd back to {source_path}")
                    else:
                        raise ShellSyntaxError(f"Command {command} doesn't support undo operation")
                    self.logger.info("SUCCESS: undo completed")
                    stack_unit.pop()
                except ShellSyntaxError as e:
                    self.logger.info("ERROR: undo failed - ShellSyntaxError")
                    print(f"ShellSyntaxError: {e}")
                except Exception as e:
                    self.logger.info("ERROR: undo failed - Unexpected exception")
                    print("Unexpected exception appeared", e)
            if stack_unit ==[]:
                self.command_stack.pop()
                self.remove_last_line(HISTORY_PATH)
                self.remove_last_line(HISTORY_PATH)
        except ShellSyntaxError as e:
            self.logger.info("ERROR: undo failed - ShellSyntaxError")
            print(f"ShellSyntaxError: {e}")
        except Exception:
            self.logger.info("ERROR: undo failed - Unexpected exception")
            print("Unexpected exception appeared")

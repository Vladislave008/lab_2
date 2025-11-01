import tempfile
import os
from unittest.mock import Mock, patch
from src.shell import Shell

class TestParsing:
    def setup_method(self):
        self.mock_logger = Mock()
        self.shell = Shell()
        self.shell.logger = self.mock_logger
        self.shell.executor = Mock()
        self.temp_history = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8')
        self.temp_history.close()
        self.history_patch = patch('src.constants.HISTORY_PATH', self.temp_history.name)
        self.history_patch.start()

    def teardown_method(self):
        self.history_patch.stop()
        if os.path.exists(self.temp_history.name):
            os.unlink(self.temp_history.name)

    def assert_parse_result(self, line, expected_command, expected_options, expected_args):
        '''Вспомогательный метод для проверки парсинга'''
        with patch.object(self.shell.executor, f'execute_{expected_command}') as mock_execute:
            self.shell.parse_line(line)
            mock_execute.assert_called_once_with(expected_options, expected_args)

    def test_basic_command_parsing(self):
        '''Тест базового парсинга команды без аргументов'''
        self.assert_parse_result('pwd', 'pwd', [], [])

    def test_command_with_single_arg(self):
        '''Тест команды с одним аргументом'''
        with patch('os.path.abspath', return_value='/absolute/path'), \
            patch('os.path.normpath', return_value='/absolute/path'):
            self.assert_parse_result('ls /home', 'ls', [], ['/absolute/path'])

    def test_command_with_options(self):
        '''Тест команды с опциями'''
        self.assert_parse_result('ls -l -a', 'ls', ['-l', '-a'], [])

    def test_command_with_options_and_args(self):
        '''Тест команды с опциями и аргументами'''
        with patch('os.path.abspath', return_value='/absolute/path'), \
            patch('os.path.normpath', return_value='/absolute/path'):
            self.assert_parse_result('ls -l /home', 'ls', ['-l'], ['/absolute/path'])

    def test_duplicate_options_removed(self):
        '''Тест удаления дублирующихся опций'''
        self.assert_parse_result('ls -l -l -a -l', 'ls', ['-l', '-a'], [])

    def test_grep_handling(self):
        '''Тест специальной обработки для grep'''
        with patch('os.path.abspath', return_value='/absolute/path'), \
            patch('os.path.normpath', return_value='/absolute/path'):
            self.assert_parse_result('grep "pattern" /file', 'grep', [], ["pattern", '/absolute/path'])

    def test_history_handling(self):
        '''Тест специальной обработки для history'''
        self.assert_parse_result('history 10', 'history', [], ['10'])

    def test_complex_grep_command(self):
        '''Тест сложной команды grep с опциями'''
        with patch('os.path.abspath', return_value='/absolute/path'), \
            patch('os.path.normpath', return_value='/absolute/path'):
            self.assert_parse_result('grep -r -i "search pattern" /path/', 'grep', ['-r', '-i'], ["search pattern", '/absolute/path'])

    def test_option_after_argument_error(self):
        '''Тест ошибки с опцией после аргумента'''
        with patch.object(self.shell.executor, 'execute_ls') as mock_execute:
            self.shell.parse_line('ls /path -l')
            mock_execute.assert_not_called()
            self.mock_logger.info.assert_called_with('ERROR: Option after argument')

    def test_all_commands_parsing(self):
        '''Тест парсинга разных команд'''
        test_cases = [
            ('ls', 'ls'),
            ('cd /home', 'cd'),
            ('cat file.txt', 'cat'),
            ('cp src dst', 'cp'),
            ('mv src dst', 'mv'),
            ('rm file', 'rm'),
            ('zip folder archive.zip', 'zip'),
            ('unzip archive.zip', 'unzip'),
            ('tar folder archive.tar', 'tar'),
            ('untar archive.tar', 'untar'),
            ('grep pattern file', 'grep'),
            ('history', 'history'),
            ('undo', 'undo'),
            ('pwd', 'pwd'),
            ('touch file', 'touch'),
            ('help', 'help')
        ]
        for command_line, expected_command in test_cases:
            with patch.object(self.shell.executor, f'execute_{expected_command}') as mock_execute, \
                patch('os.path.abspath', return_value='/absolute/path'), \
                patch('os.path.normpath', return_value='/absolute/path'), \
                patch('os.path.expanduser', return_value='/absolute/path'):
                self.shell.parse_line(command_line)
                mock_execute.assert_called_once()

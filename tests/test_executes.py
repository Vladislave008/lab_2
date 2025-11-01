import unittest
from src.shell import Shell
from unittest import mock
from pyfakefs.fake_filesystem_unittest import TestCase # type: ignore[import]
import os
from io import StringIO
import sys
from src.command_execute import CommandExecutor

class TestExecutes(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.shell = Shell()
        self.shell.executor = CommandExecutor(self.shell.logger)

    def capture_output(self, func):
        '''Вспомогательная функция для захвата вывода'''
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            func()
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

    def test_ls_basic(self):
        '''Тест ls - создаём файлы и проверяем вывод'''
        self.fs.create_file('file1.txt')
        self.fs.create_file('file2.txt')
        self.fs.create_dir('test_dir')
        output = self.capture_output(lambda: self.shell.executor.execute_ls([], []))
        self.assertIn('file1.txt', output)
        self.assertIn('file2.txt', output)
        self.assertIn('test_dir', output)

    def test_cd_and_pwd(self):
        '''Тест cd и pwd'''
        self.fs.create_dir('subdir')
        start_dir = os.getcwd()
        self.shell.executor.execute_cd([], ['subdir'])
        cur_dir = self.capture_output(lambda: self.shell.executor.execute_pwd([],[]))
        cur_dir = cur_dir.strip()
        self.assertTrue(cur_dir.endswith('subdir'))
        self.shell.executor.execute_cd([], ['..'])
        cur_dir = self.capture_output(lambda: self.shell.executor.execute_pwd([],[]))
        cur_dir = cur_dir.strip()
        self.assertEqual(cur_dir, start_dir)

    def test_touch_and_cat(self):
        '''Тест создания файла и чтения'''
        self.shell.executor.execute_touch([], ['test_file.txt'])
        self.assertTrue(os.path.exists('test_file.txt'))
        with open('test_file.txt', 'w') as f:
            f.write('hello world\nline two')
        output = self.capture_output(lambda: self.shell.executor.execute_cat([], ['test_file.txt']))
        self.assertIn('hello world', output)
        self.assertIn('line two', output)

    def test_cp_file(self):
        '''Тест копирования файла'''
        self.fs.create_file('source file.txt', contents='test content')
        self.shell.executor.execute_cp([], ['source file.txt', 'dest file.txt'], False)
        self.assertTrue(os.path.exists('dest file.txt'))
        with open('dest file.txt', 'r') as f:
            self.assertEqual(f.read(), 'test content')

    def test_mv_file(self):
        '''Тест перемещения файла'''
        self.fs.create_file('old_name.txt', contents='content')
        self.shell.executor.execute_mv([], ['old_name.txt', 'new_name.txt'], False)
        self.assertFalse(os.path.exists('old_name.txt'))
        self.assertTrue(os.path.exists('new_name.txt'))
        with open('new_name.txt', 'r') as f:
            self.assertEqual(f.read(), 'content')

    def test_rm_file(self):
        '''Тест удаления файла'''
        self.fs.create_file('to_delete.txt')
        with mock.patch('builtins.input', return_value='y'):
            self.shell.executor.execute_rm([], ['to_delete.txt'], False)
        self.assertFalse(os.path.exists('to_delete.txt'))

    def test_zip_and_unzip(self):
        '''Тест архивации и распаковки'''
        self.fs.create_file('test.txt', contents='zip')
        self.shell.executor.execute_zip([], ['test.txt', 'archive.zip'])
        self.assertTrue(os.path.exists('archive.zip'))
        os.remove('test.txt')
        self.assertFalse(os.path.exists('test.txt'))
        self.shell.executor.execute_unzip([], ['archive.zip'])
        self.assertTrue(os.path.exists('test.txt'))
        with open('test.txt', 'r') as f:
            self.assertEqual(f.read(), 'zip')

    def test_grep_in_file(self):
        '''Тест поиска в файле'''
        self.fs.create_file('grep test.txt', contents='first line\npattern here\nthird line\nanother pattern')
        output = self.capture_output(lambda:
            self.shell.executor.execute_grep([], ['pattern', 'grep test.txt']))
        self.assertIn('pattern here', output)
        self.assertIn('another pattern', output)
        self.assertNotIn('first line', output)

        self.fs.create_file('grep test 2.txt', contents='first line\npatTern here\nthird line pattern\nanother paTTern')
        output = self.capture_output(lambda:
            self.shell.executor.execute_grep(['-i'], ['pattern', 'grep test 2.txt']))
        self.assertIn('patTern here', output)
        self.assertIn('another paTTern', output)
        self.assertIn('third line', output)
        self.assertNotIn('first line', output)

        self.fs.create_file('grep test 3.txt', contents='first line\npatTern here\nthird line pattern\nanother paTTern')
        output = self.capture_output(lambda:
            self.shell.executor.execute_grep([], ['pattern', 'grep test 3.txt']))
        self.assertNotIn('patTern here', output)
        self.assertNotIn('another paTTern', output)
        self.assertIn('third line', output)
        self.assertNotIn('first line', output)

    def test_undo_rm(self):
        '''Тест отмены удаления'''
        self.fs.create_file('undo_test.txt', contents='important data')
        with mock.patch('builtins.input', return_value='y'):
            self.shell.executor.execute_rm([], ['undo_test.txt'], False)
        self.assertFalse(os.path.exists('undo_test.txt'))
        self.shell.executor.execute_undo([], [])
        self.assertTrue(os.path.exists('undo_test.txt'))
        with open('undo_test.txt', 'r') as f:
            self.assertEqual(f.read(), 'important data')

    def test_undo_cp_with_overwrite(self):
        '''Тест отмены копирования с перезаписью файла'''
        self.fs.create_file('source.txt', contents='source content')
        self.fs.create_file('target.txt', contents='target content')
        self.shell.executor.execute_cp([], ['source.txt', 'target.txt'], False)
        with open('target.txt', 'r') as f:
            self.assertEqual(f.read(), 'source content')
        self.shell.executor.execute_undo([], [])
        with open('target.txt', 'r') as f:
            self.assertEqual(f.read(), 'target content')

    def test_undo_mv_with_overwrite(self):
        '''Тест отмены перемещения с перезаписью файла'''
        self.fs.create_file('source.txt', contents='source content')
        self.fs.create_file('target.txt', contents='target content')
        self.shell.executor.execute_mv([], ['source.txt', 'target.txt'], False)
        self.assertFalse(os.path.exists('source.txt'))
        with open('target.txt', 'r') as f:
            self.assertEqual(f.read(), 'source content')
        self.shell.executor.execute_undo([], [])
        self.assertTrue(os.path.exists('source.txt'))
        self.assertTrue(os.path.exists('target.txt'))
        with open('source.txt', 'r') as f:
            self.assertEqual(f.read(), 'source content')
        with open('target.txt', 'r') as f:
            self.assertEqual(f.read(), 'target content')

    def test_undo_multiple_operations(self):
        '''Тест отмены нескольких операций'''
        self.fs.create_file('file1.txt', contents='content1')
        self.fs.create_file('file2.txt', contents='content2')

        self.shell.executor.execute_cp([], ['file1.txt', 'copy.txt'], False)

        with mock.patch('builtins.input', return_value='y'):
            self.shell.executor.execute_rm([], ['file2.txt'], False)

        self.shell.executor.execute_mv([], ['file1.txt', 'moved.txt'], False)

        self.assertFalse(os.path.exists('file1.txt'))
        self.assertFalse(os.path.exists('file2.txt'))
        self.assertTrue(os.path.exists('moved.txt'))
        self.assertTrue(os.path.exists('copy.txt'))

        self.shell.executor.execute_undo([], [])
        self.assertTrue(os.path.exists('file1.txt'))
        self.assertFalse(os.path.exists('file2.txt'))

        self.shell.executor.execute_undo([], [])
        self.assertTrue(os.path.exists('file2.txt'))

        self.shell.executor.execute_undo([], [])
        self.assertFalse(os.path.exists('copy.txt'))

    # ERROR-CASES

    def test_rm_nonexistent_file(self):
        '''Тест удаления несуществующего файла'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_rm([], ['nonexistent.txt'], False))
        self.assertIn('FileNotFoundError', output)
        self.assertIn("doesn't exist", output)

    def test_cp_nonexistent_source(self):
        '''Тест копирования несуществующего файла'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_cp([], ['nonexistent.txt', 'target.txt'], False))
        self.assertIn('FileNotFoundError', output)
        self.assertIn("doesn't exist", output)

    def test_mv_nonexistent_source(self):
        '''Тест перемещения несуществующего файла'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_mv([], ['nonexistent.txt', 'target.txt'], False))
        self.assertIn('FileNotFoundError', output)
        self.assertIn("doesn't exist", output)

    def test_cd_nonexistent_directory(self):
        '''Тест перехода в несуществующую директорию'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_cd([], ['nonexistent_dir']))
        self.assertIn('FileNotFoundError', output)
        self.assertIn("doesn't exist", output)

    def test_cat_nonexistent_file(self):
        '''Тест чтения несуществующего файла'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_cat([], ['nonexistent.txt']))
        self.assertIn('FileNotFoundError', output)
        self.assertIn("doesn't exist", output)

    def test_cat_directory_instead_of_file(self):
        '''Тест чтения директории вместо файла'''
        self.fs.create_dir('test_dir')
        output = self.capture_output(lambda:
            self.shell.executor.execute_cat([], ['test_dir']))
        self.assertIn('IsADirectoryError', output)
        self.assertIn('only files', output)

    def test_rm_dangerous_path(self):
        '''Тест удаления защищённого пути'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_rm([], ['/'], False))
        self.assertIn('ShellSyntaxError', output)
        self.assertIn('crash', output)

        output = self.capture_output(lambda:
            self.shell.executor.execute_rm([], ['..'], False))
        self.assertIn('ShellSyntaxError', output)
        self.assertIn('crash', output)

    def test_invalid_command_syntax(self):
        '''Тест некорректного синтаксиса команд'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_ls([], ['arg1', 'arg2']))
        self.assertIn('ShellSyntaxError', output)
        output = self.capture_output(lambda:
            self.shell.executor.execute_cp([], ['only_one_arg'], False))
        self.assertIn('ShellSyntaxError', output)

    def test_undo_empty_stack(self):
        '''Тест отмены при пустом стеке команд'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_undo([], []))
        self.assertIn('ShellSyntaxError', output)
        self.assertIn('empty', output)

    def test_rm_cancel_confirmation(self):
        '''Тест отмены удаления при ответе "n"'''
        self.fs.create_file('to_cancel.txt')
        with mock.patch('builtins.input', return_value='n'):
            self.capture_output(lambda:
                self.shell.executor.execute_rm([], ['to_cancel.txt'], False))
        self.assertTrue(os.path.exists('to_cancel.txt'))

    def test_invalid_options(self):
        '''Тест невалидных опций команд'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_ls(['--invalid-option'], []))
        self.assertIn('ShellSyntaxError', output)
        output = self.capture_output(lambda:
            self.shell.executor.execute_cp(['-x'], ['src.txt', 'dst.txt'], False))
        self.assertIn('ShellSyntaxError', output)

    def test_zip_unzip_nonexistent(self):
        '''Тест архивации несуществующих файлов'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_zip([], ['nonexistent', 'archive.zip']))
        self.assertIn('FileNotFoundError', output)
        self.assertIn("doesn't exist", output)
        output = self.capture_output(lambda:
            self.shell.executor.execute_unzip([], ['nonexistent.zip']))
        self.assertIn('FileNotFoundError', output)
        self.assertIn("doesn't exist", output)

    def test_grep_in_nonexistent_file(self):
        '''Тест поиска в несуществующем файле'''
        output = self.capture_output(lambda:
            self.shell.executor.execute_grep([], ['pattern', 'nonexistent.txt']))
        self.assertIn('FileNotFoundError', output)
        self.assertIn("doesn't exist", output)

if __name__ == '__main__':
    unittest.main()

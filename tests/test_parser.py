import pytest
from pathlib import Path
from src.parser import load_gitignore, find_files, parse_file, ParserError

def test_load_gitignore(tmp_path):
    # Test loading gitignore patterns
    gitignore_content = """
# This is a comment
*.log
/build/
dist/
"""
    gitignore_file = tmp_path / ".gitignore"
    gitignore_file.write_text(gitignore_content)
    
    spec = load_gitignore(tmp_path)
    assert spec is not None
    assert spec.match_file("test.log") is True
    assert spec.match_file("src/test.log") is True
    assert spec.match_file("build/") is True
    assert spec.match_file("dist/file.py") is True
    assert spec.match_file("src/main.py") is False

def test_load_gitignore_missing(tmp_path):
    # Test return value when gitignore is missing
    spec = load_gitignore(tmp_path)
    assert spec is None

def test_find_files(tmp_path):
    # Setup files in tmp_path
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "utils.py").write_text("def util(): pass")
    
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "test.js").write_text("console.log('test')")
    
    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "pip.py").write_text("import sys")
    
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "output.py").write_text("pass")
    
    (tmp_path / ".gitignore").write_text("*.log\ntemp/")
    (tmp_path / "test.log").write_text("log data")
    
    (tmp_path / "temp").mkdir()
    (tmp_path / "temp" / "temp.py").write_text("pass")

    files = find_files(tmp_path)
    
    # Resolve and convert to relative strings for comparison
    rel_files = {str(f.relative_to(tmp_path).as_posix()) for f in files}
    
    assert "src/main.py" in rel_files
    assert "src/utils.py" in rel_files
    assert ".gitignore" in rel_files
    
    # Ignored directories and files should not be present
    assert "node_modules/test.js" not in rel_files
    assert "venv/pip.py" not in rel_files
    assert "build/output.py" not in rel_files
    assert "test.log" not in rel_files
    assert "temp/temp.py" not in rel_files

def test_find_files_extra_excludes(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "utils.py").write_text("def util(): pass")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("doc")

    files = find_files(tmp_path, extra_excludes=["docs/", "src/utils.py"])
    rel_files = {str(f.relative_to(tmp_path).as_posix()) for f in files}
    
    assert "src/main.py" in rel_files
    assert "src/utils.py" not in rel_files
    assert "docs/README.md" not in rel_files

def test_parse_file_python(tmp_path):
    py_file = tmp_path / "test.py"
    py_file.write_text("def hello() -> str:\n    return 'world'")
    
    ast_tree = parse_file(py_file)
    assert ast_tree is not None

def test_parse_file_unsupported(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello world")
    
    with pytest.raises(NotImplementedError):
        parse_file(txt_file)

def test_parse_file_syntax_error(tmp_path):
    invalid_py = tmp_path / "invalid.py"
    invalid_py.write_text("def hello(invalid syntax")
    
    with pytest.raises(ParserError):
        parse_file(invalid_py)

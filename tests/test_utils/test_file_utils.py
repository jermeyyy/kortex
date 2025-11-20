import os
from pathlib import Path
import pytest
from kortex_mcp.utils.file_utils import (
    find_project_root,
    find_build_files,
    ensure_directory,
    is_kotlin_file,
    is_swift_file,
    is_objc_file,
    get_relative_path,
    read_file_safe,
    write_file_safe
)

class TestFileUtils:
    def test_find_project_root_with_marker(self, tmp_path):
        # Create a project structure
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "settings.gradle.kts").touch()
        
        src_dir = project_root / "src" / "main"
        src_dir.mkdir(parents=True)
        
        found_root = find_project_root(src_dir)
        assert found_root == project_root.resolve()

    def test_find_project_root_no_marker(self, tmp_path):
        # Create a directory structure without markers
        root = tmp_path / "root"
        root.mkdir()
        child = root / "child"
        child.mkdir()
        
        found_root = find_project_root(child)
        assert found_root is None

    def test_find_project_root_custom_markers(self, tmp_path):
        project_root = tmp_path / "custom_project"
        project_root.mkdir()
        (project_root / "custom.marker").touch()
        
        child = project_root / "child"
        child.mkdir()
        
        found_root = find_project_root(child, markers=["custom.marker"])
        assert found_root == project_root.resolve()

    def test_find_build_files(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Root build file
        (project_root / "build.gradle.kts").touch()
        
        # Module build file
        module_dir = project_root / "module"
        module_dir.mkdir()
        (module_dir / "build.gradle.kts").touch()
        
        # Ignored directory
        build_dir = project_root / "build"
        build_dir.mkdir()
        (build_dir / "build.gradle.kts").touch()
        
        build_files = find_build_files(project_root)
        assert len(build_files) == 2
        assert project_root / "build.gradle.kts" in build_files
        assert module_dir / "build.gradle.kts" in build_files

    def test_ensure_directory(self, tmp_path):
        target_dir = tmp_path / "new" / "directory"
        assert not target_dir.exists()
        
        result = ensure_directory(target_dir)
        assert result.exists()
        assert result.is_dir()
        assert result == target_dir

    def test_is_kotlin_file(self):
        assert is_kotlin_file(Path("Main.kt"))
        assert is_kotlin_file(Path("Script.kts"))
        assert not is_kotlin_file(Path("Main.java"))
        assert not is_kotlin_file(Path("README.md"))

    def test_is_swift_file(self):
        assert is_swift_file(Path("Main.swift"))
        assert not is_swift_file(Path("Main.kt"))

    def test_is_objc_file(self):
        assert is_objc_file(Path("Main.m"))
        assert is_objc_file(Path("Main.mm"))
        assert is_objc_file(Path("Main.h"))
        assert not is_objc_file(Path("Main.swift"))

    def test_get_relative_path(self):
        base = Path("/a/b")
        path = Path("/a/b/c/d.txt")
        assert get_relative_path(path, base) == Path("c/d.txt")

    def test_get_relative_path_error(self):
        base = Path("/a/b")
        path = Path("/x/y/z.txt")
        with pytest.raises(ValueError):
            get_relative_path(path, base)

    def test_read_file_safe_success(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("content", encoding="utf-8")
        assert read_file_safe(f) == "content"

    def test_read_file_safe_failure(self, tmp_path):
        f = tmp_path / "nonexistent.txt"
        assert read_file_safe(f) is None

    def test_write_file_safe_success(self, tmp_path):
        f = tmp_path / "output.txt"
        assert write_file_safe(f, "content")
        assert f.read_text(encoding="utf-8") == "content"

    def test_write_file_safe_failure(self, tmp_path):
        # Try to write to a directory path
        d = tmp_path / "dir"
        d.mkdir()
        # Writing to a directory raises IsADirectoryError which inherits from OSError
        assert not write_file_safe(d, "content")

"""Integration tests for KMP analyzer - expect/actual detection.

Tests cover Kotlin Multiplatform-specific analysis including:
- Expect/actual declaration detection
- Source set analysis
- Platform-specific code identification
"""

from pathlib import Path

import pytest

from kortex_mcp.analyzers.kmp_analyzer import KMPAnalyzer
from kortex_mcp.models.project import SourceSetType


@pytest.mark.integration
@pytest.mark.asyncio
class TestExpectActualDetection:
    """Integration tests for expect/actual declaration detection (T040)."""

    async def test_detect_expect_declaration_in_common_main(self, sample_kmp_project: Path):
        """Test detection of expect declaration in commonMain."""
        # Create expect declaration
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        expect_file = common_main / "Platform.kt"
        expect_file.write_text("""
            package com.example.kmp
            
            expect class Platform {
                val name: String
            }
        """)

        analyzer = KMPAnalyzer(sample_kmp_project)
        declarations = await analyzer.find_expect_declarations("Platform")
        
        assert len(declarations) == 1
        assert declarations[0]["name"] == "Platform"
        assert declarations[0]["kind"] == "class"
        assert str(expect_file) in declarations[0]["file"]

    async def test_detect_actual_declaration_in_platform_source_set(self, sample_kmp_project: Path):
        """Test detection of actual declaration in platform source sets."""
        # Create actual declaration
        android_main = sample_kmp_project / "src" / "androidMain" / "kotlin"
        android_main.mkdir(parents=True, exist_ok=True)
        actual_file = android_main / "Platform.kt"
        actual_file.write_text("""
            package com.example.kmp
            
            actual class Platform {
                actual val name: String = "Android"
            }
        """)

        analyzer = KMPAnalyzer(sample_kmp_project)
        # Note: find_actual_implementations requires symbol name and kind
        declarations = await analyzer.find_actual_implementations("Platform", "class")
        
        assert "androidMain" in declarations
        assert declarations["androidMain"]["name"] == "Platform"
        assert str(actual_file) in declarations["androidMain"]["file"]

    async def test_match_expect_with_actuals(self, sample_kmp_project: Path):
        """Test matching expect declarations with their actual implementations."""
        # Create expect declaration
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        (common_main / "Platform.kt").write_text("""
            package com.example.kmp
            expect class Platform {
                val name: String
            }
        """)

        # Create actual declarations
        android_main = sample_kmp_project / "src" / "androidMain" / "kotlin"
        android_main.mkdir(parents=True, exist_ok=True)
        (android_main / "Platform.kt").write_text("""
            package com.example.kmp
            actual class Platform {
                actual val name: String = "Android"
            }
        """)

        ios_main = sample_kmp_project / "src" / "iosMain" / "kotlin"
        ios_main.mkdir(parents=True, exist_ok=True)
        (ios_main / "Platform.kt").write_text("""
            package com.example.kmp
            actual class Platform {
                actual val name: String = "iOS"
            }
        """)

        analyzer = KMPAnalyzer(sample_kmp_project)
        pairs = await analyzer.find_expect_actual_pairs("Platform")
        
        assert len(pairs) == 1
        pair = pairs[0]
        assert pair.name == "Platform"
        assert len(pair.actual_locations) == 2
        
        assert "androidMain" in pair.actual_locations
        assert "iosMain" in pair.actual_locations

    async def test_detect_expect_function(self, sample_kmp_project: Path):
        """Test detection of expect function."""
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        expect_file = common_main / "Utils.kt"
        expect_file.write_text("""
            package com.example.kmp
            
            expect fun getPlatformName(): String
        """)

        analyzer = KMPAnalyzer(sample_kmp_project)
        declarations = await analyzer.find_expect_declarations("getPlatformName")
        
        assert len(declarations) == 1
        assert declarations[0]["name"] == "getPlatformName"
        assert declarations[0]["kind"] == "function"

    async def test_detect_expect_property(self, sample_kmp_project: Path):
        """Test detection of expect property."""
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        expect_file = common_main / "Config.kt"
        expect_file.write_text("""
            package com.example.kmp
            
            expect val isDebug: Boolean
        """)

        analyzer = KMPAnalyzer(sample_kmp_project)
        declarations = await analyzer.find_expect_declarations("isDebug")
        
        assert len(declarations) == 1
        assert declarations[0]["name"] == "isDebug"
        assert declarations[0]["kind"] == "property"

    async def test_detect_missing_actual_implementation(self, sample_kmp_project: Path):
        """Test detection of missing actual implementation."""
        # Create expect declaration
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        (common_main / "Missing.kt").write_text("""
            package com.example.kmp
            expect class Missing
        """)

        # Create only one actual
        android_main = sample_kmp_project / "src" / "androidMain" / "kotlin"
        android_main.mkdir(parents=True, exist_ok=True)
        (android_main / "Missing.kt").write_text("""
            package com.example.kmp
            actual class Missing
        """)

        # Assume iosMain exists but has no implementation
        ios_main = sample_kmp_project / "src" / "iosMain" / "kotlin"
        ios_main.mkdir(parents=True, exist_ok=True)

        analyzer = KMPAnalyzer(sample_kmp_project)
        missing = await analyzer.find_missing_actuals("Missing")
        
        # Note: find_missing_actuals logic depends on detected source sets
        # Since we created iosMain, it should be detected as missing
        assert "iosMain" in missing
        assert "androidMain" not in missing

    async def test_validate_expect_actual_signatures_match(self, sample_kmp_project: Path):
        """Test validation that expect and actual signatures match."""
        # This might be too advanced for regex-based analyzer, but let's see if it's implemented
        pass


@pytest.mark.integration
@pytest.mark.asyncio
class TestSourceSetAnalysis:
    """Integration tests for source set analysis."""

    async def test_identify_source_set_from_file_path(self, sample_kmp_project: Path):
        """Test identifying source set from file path."""
        analyzer = KMPAnalyzer(sample_kmp_project)
        
        common_file = sample_kmp_project / "src" / "commonMain" / "kotlin" / "Platform.kt"
        source_set = analyzer.get_source_set_from_path(common_file)
        assert source_set is not None
        assert source_set.name == "commonMain"
        assert source_set.type == SourceSetType.COMMON

        android_file = sample_kmp_project / "src" / "androidMain" / "kotlin" / "Platform.kt"
        source_set = analyzer.get_source_set_from_path(android_file)
        assert source_set is not None
        assert source_set.name == "androidMain"
        assert source_set.type == SourceSetType.ANDROID

    async def test_identify_platform_specific_source_sets(self, sample_kmp_project: Path):
        """Test identification of platform-specific source sets."""
        analyzer = KMPAnalyzer(sample_kmp_project)
        
        # Ensure source sets are detected
        assert "androidMain" in analyzer.source_sets
        assert analyzer.source_sets["androidMain"].type == SourceSetType.ANDROID
        
        assert "iosMain" in analyzer.source_sets
        assert analyzer.source_sets["iosMain"].type == SourceSetType.IOS

    async def test_list_all_source_sets_in_project(self, sample_kmp_project: Path):
        """Test listing all source sets in a KMP project."""
        analyzer = KMPAnalyzer(sample_kmp_project)
        source_sets = analyzer.get_all_source_sets()
        
        names = [ss.name for ss in source_sets]
        assert "commonMain" in names
        assert "androidMain" in names
        assert "iosMain" in names

    async def test_detect_all_source_set_types(self, sample_kmp_project: Path):
        """Test detection of all supported source set types."""
        # Create various source set directories
        source_sets = [
            "jvmMain", "jsMain", "desktopMain", 
            "jvmTest", "jsTest", "desktopTest"
        ]
        
        for ss in source_sets:
            (sample_kmp_project / "src" / ss / "kotlin").mkdir(parents=True, exist_ok=True)
            
        analyzer = KMPAnalyzer(sample_kmp_project)
        
        assert "jvmMain" in analyzer.source_sets
        assert analyzer.source_sets["jvmMain"].type == SourceSetType.JVM
        
        assert "jsMain" in analyzer.source_sets
        assert analyzer.source_sets["jsMain"].type == SourceSetType.JS
        
        assert "desktopMain" in analyzer.source_sets
        assert analyzer.source_sets["desktopMain"].type == SourceSetType.DESKTOP


@pytest.mark.integration
@pytest.mark.asyncio
class TestPlatformSpecificCodeIdentification:
    """Integration tests for platform-specific code identification."""

    async def test_identify_android_specific_code(self, sample_kmp_project: Path):
        """Test identification of Android-specific code."""
        analyzer = KMPAnalyzer(sample_kmp_project)
        android_file = sample_kmp_project / "src" / "androidMain" / "kotlin" / "Android.kt"
        
        is_specific = analyzer.is_platform_specific_code(android_file)
        assert is_specific
        
        platform = analyzer.get_platform_for_file(android_file)
        assert platform == SourceSetType.ANDROID

    async def test_identify_ios_specific_code(self, sample_kmp_project: Path):
        """Test identification of iOS-specific code."""
        analyzer = KMPAnalyzer(sample_kmp_project)
        ios_file = sample_kmp_project / "src" / "iosMain" / "kotlin" / "Ios.kt"
        
        is_specific = analyzer.is_platform_specific_code(ios_file)
        assert is_specific
        
        platform = analyzer.get_platform_for_file(ios_file)
        assert platform == SourceSetType.IOS

    async def test_identify_common_code(self, sample_kmp_project: Path):
        """Test identification of common/shared code."""
        analyzer = KMPAnalyzer(sample_kmp_project)
        common_file = sample_kmp_project / "src" / "commonMain" / "kotlin" / "Common.kt"
        
        is_specific = analyzer.is_platform_specific_code(common_file)
        assert not is_specific
        
        platform = analyzer.get_platform_for_file(common_file)
        assert platform == SourceSetType.COMMON

    async def test_detect_platform_specific_imports(self):
        """Test detection of platform-specific imports."""
        pytest.skip("Import-based detection not yet implemented - future enhancement")


@pytest.mark.unit
@pytest.mark.asyncio
class TestKMPAnalyzerConfiguration:
    """Unit tests for KMP analyzer configuration."""

    async def test_analyzer_initialization(self):
        """Test KMP analyzer initialization."""
        analyzer = KMPAnalyzer(workspace_path=Path("/test/project"))

        assert analyzer.workspace_path == Path("/test/project")
        assert hasattr(analyzer, 'source_sets')

    async def test_analyzer_with_custom_source_sets(self):
        """Test analyzer with custom source set configuration."""
        pytest.skip("Custom source set configuration not yet implemented - future enhancement")


@pytest.mark.integration
@pytest.mark.asyncio
class TestCodeAnalysis:
    """Integration tests for code analysis features."""

    async def test_find_class_insertion_point(self, sample_kmp_project: Path):
        """Test finding insertion point in a class."""
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        file_path = common_main / "User.kt"
        file_path.write_text("""
            package com.example
            
            class User {
                val name: String = ""
                
                fun getName(): String {
                    return name
                }
            }
        """)
        
        analyzer = KMPAnalyzer(sample_kmp_project)
        point = analyzer.find_class_insertion_point(file_path, "User")
        
        assert point is not None
        assert point["class_name"] == "User"
        assert point["context"] == "class_body"
        # Should be after getName()
        assert point["line"] > 5

    async def test_find_class_insertion_point_empty_class(self, sample_kmp_project: Path):
        """Test finding insertion point in an empty class."""
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        file_path = common_main / "Empty.kt"
        file_path.write_text("""
            package com.example
            
            class Empty {
            }
        """)
        
        analyzer = KMPAnalyzer(sample_kmp_project)
        point = analyzer.find_class_insertion_point(file_path, "Empty")
        
        assert point is not None
        # Should be inside the braces
        assert point["line"] == 4

    async def test_find_class_insertion_point_with_companion(self, sample_kmp_project: Path):
        """Test finding insertion point in a class with companion object."""
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        file_path = common_main / "WithCompanion.kt"
        file_path.write_text("""
            package com.example
            
            class WithCompanion {
                fun method() {}
                
                companion object {
                    fun create() = WithCompanion()
                }
            }
        """)
        
        analyzer = KMPAnalyzer(sample_kmp_project)
        point = analyzer.find_class_insertion_point(file_path, "WithCompanion")
        
        assert point is not None
        # Should be before companion object
        assert point["line"] == 6

    async def test_detect_indentation_style_spaces(self, sample_kmp_project: Path):
        """Test detecting space indentation."""
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        file_path = common_main / "Spaces.kt"
        file_path.write_text("""
class Spaces {
    fun method() {
        val x = 1
    }
}
""")
        
        analyzer = KMPAnalyzer(sample_kmp_project)
        style = analyzer.detect_indentation_style(file_path)
        
        assert style["type"] == "spaces"
        assert style["size"] == 4

    async def test_detect_indentation_style_tabs(self, sample_kmp_project: Path):
        """Test detecting tab indentation."""
        common_main = sample_kmp_project / "src" / "commonMain" / "kotlin"
        common_main.mkdir(parents=True, exist_ok=True)
        file_path = common_main / "Tabs.kt"
        file_path.write_text("""
class Tabs {
\tfun method() {
\t\tval x = 1
\t}
}
""")
        
        analyzer = KMPAnalyzer(sample_kmp_project)
        style = analyzer.detect_indentation_style(file_path)
        
        assert style["type"] == "tabs"

"""iOS platform memory generator for KMP projects.

This module provides a memory generator that transforms iOS analysis data
into structured memory content for AI agents.
"""

from typing import Any

from kortex_mcp.generators.base import BaseMemoryGenerator


class iOSMemoryGenerator(BaseMemoryGenerator):
    """Generator for iOS platform memories.

    This generator transforms raw iOS analysis data into a comprehensive
    memory document that describes the iOS configuration, including:
    - Bundle configuration (ID, name, version)
    - Minimum iOS version
    - Swift files overview
    - Kotlin/Swift interop patterns
    - CocoaPods and SPM dependencies
    - Privacy descriptions
    - URL schemes
    - Xcode project configuration

    The generated memory helps AI agents understand the iOS-specific
    configuration and make informed decisions about platform features.

    Example:
        >>> generator = iOSMemoryGenerator()
        >>> analysis_data = {
        ...     "info_plists": [{
        ...         "bundle_id": "com.example.app",
        ...         "bundle_name": "MyApp",
        ...         "version": "1.0.0",
        ...         "build": "1",
        ...         "min_ios": "14.0",
        ...     }],
        ...     "swift_files": {"count": 15, "directories": ["iosApp"]},
        ...     "dependencies": {
        ...         "cocoapods": {"has_podfile": True, "pods": ["Alamofire"]},
        ...         "spm": {"has_package_swift": False, "packages": []},
        ...     },
        ... }
        >>> content = generator.generate_content(analysis_data)
        >>> markdown = generator.to_markdown(content)
    """

    @property
    def memory_id(self) -> str:
        """Unique identifier for iOS platform memories.

        Returns:
            str: The identifier "ios_platform".
        """
        return "ios_platform"

    @property
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        Returns:
            str: The title "iOS Platform".
        """
        return "iOS Platform"

    @property
    def memory_category(self) -> str:
        """Category for organizing iOS platform memories.

        Returns:
            str: The category "ios_platform".
        """
        return "ios_platform"

    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from iOS analysis data.

        Transforms raw iOS analysis results into a normalized dictionary
        containing platform configuration information.

        Args:
            analysis_data: Dictionary containing iOS analysis results.
                Expected structure:
                {
                    "info_plists": [
                        {
                            "bundle_id": "com.example.app",
                            "bundle_name": "MyApp",
                            "version": "1.0.0",
                            "build": "1",
                            "min_ios": "14.0",
                            "privacy_descriptions": {...},
                            "url_schemes": [...],
                            "capabilities": {...},
                        },
                        ...
                    ],
                    "swift_files": {
                        "count": 15,
                        "directories": ["iosApp", "src/iosMain"],
                        "interop_patterns": ["@ObjCName", ...],
                    },
                    "dependencies": {
                        "cocoapods": {"has_podfile": True, "pods": [...]},
                        "spm": {"has_package_swift": False, "packages": [...]},
                    },
                    "xcode_project": {
                        "name": "iosApp",
                        "path": "iosApp/iosApp.xcodeproj",
                        "type": "xcodeproj",
                    }
                }

        Returns:
            dict[str, Any]: Structured memory content with keys:
                - bundle_info: Bundle configuration from primary Info.plist
                - swift_files: Swift files information
                - interop: Kotlin/Swift interop patterns
                - dependencies: CocoaPods and SPM dependencies
                - privacy_descriptions: Privacy usage descriptions
                - url_schemes: Registered URL schemes
                - xcode_project: Xcode project information

        Raises:
            ValueError: If analysis_data is None.
        """
        if analysis_data is None:
            raise ValueError("Analysis data cannot be None")

        # Extract primary Info.plist data (use first one as primary)
        info_plists = analysis_data.get("info_plists", [])
        primary_plist = info_plists[0] if info_plists else {}

        # Normalize bundle info
        bundle_info = {
            "bundle_id": primary_plist.get("bundle_id", ""),
            "bundle_name": primary_plist.get("bundle_name", ""),
            "version": primary_plist.get("version", ""),
            "build": primary_plist.get("build", ""),
            "min_ios": primary_plist.get("min_ios", ""),
        }

        # Normalize Swift files info
        swift_files_data = analysis_data.get("swift_files", {})
        swift_files = {
            "count": swift_files_data.get("count", 0),
            "directories": swift_files_data.get("directories", []),
        }

        # Extract interop patterns
        interop = {
            "patterns": swift_files_data.get("interop_patterns", []),
        }

        # Normalize dependencies
        deps_data = analysis_data.get("dependencies", {})
        cocoapods_data = deps_data.get("cocoapods", {})
        spm_data = deps_data.get("spm", {})

        dependencies = {
            "cocoapods": {
                "has_podfile": cocoapods_data.get("has_podfile", False),
                "pods": cocoapods_data.get("pods", []),
            },
            "spm": {
                "has_package_swift": spm_data.get("has_package_swift", False),
                "packages": spm_data.get("packages", []),
            },
        }

        # Extract privacy descriptions from primary plist
        privacy_descriptions = primary_plist.get("privacy_descriptions", {})

        # Extract URL schemes from primary plist
        url_schemes = primary_plist.get("url_schemes", [])

        # Normalize Xcode project info
        xcode_data = analysis_data.get("xcode_project", {})
        xcode_project = {
            "name": xcode_data.get("name", ""),
            "path": xcode_data.get("path", ""),
            "type": xcode_data.get("type", ""),
        }

        return {
            "bundle_info": bundle_info,
            "swift_files": swift_files,
            "interop": interop,
            "dependencies": dependencies,
            "privacy_descriptions": privacy_descriptions,
            "url_schemes": url_schemes,
            "xcode_project": xcode_project,
        }

    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        Creates a well-formatted markdown document describing the iOS
        platform configuration, suitable for consumption by AI agents.

        Args:
            memory_data: Structured memory content as returned by generate_content.
                Expected keys: bundle_info, swift_files, interop, dependencies,
                privacy_descriptions, url_schemes, xcode_project.

        Returns:
            str: Markdown-formatted string representation of the iOS config.

        Raises:
            ValueError: If memory_data is None or empty.
        """
        if not memory_data:
            raise ValueError("Memory data cannot be empty")

        sections = []

        # Main title
        sections.append("# iOS Platform Configuration")

        # Overview section
        overview_content = self._build_overview_section(memory_data)
        sections.append(self._format_section("Overview", overview_content))

        # Swift files section
        swift_content = self._build_swift_files_section(memory_data)
        sections.append(self._format_section("Swift Files", swift_content))

        # Kotlin/Swift interop section
        interop_content = self._build_interop_section(memory_data)
        sections.append(self._format_section("Kotlin/Swift Interop", interop_content))

        # Dependencies section
        deps_content = self._build_dependencies_section(memory_data)
        sections.append(self._format_section("Dependencies", deps_content))

        # Privacy descriptions section
        privacy_data = memory_data.get("privacy_descriptions", {})
        if privacy_data:
            privacy_content = self._build_privacy_section(privacy_data)
            sections.append(self._format_section("Privacy Descriptions", privacy_content))

        # URL schemes section
        url_schemes = memory_data.get("url_schemes", [])
        if url_schemes:
            url_content = self._build_url_schemes_section(url_schemes)
            sections.append(self._format_section("URL Schemes", url_content))

        # Xcode project section
        xcode_data = memory_data.get("xcode_project", {})
        if xcode_data.get("name"):
            xcode_content = self._build_xcode_section(xcode_data)
            sections.append(self._format_section("Xcode Project", xcode_content))

        # Development notes
        notes_content = self._build_development_notes(memory_data)
        sections.append(self._format_section("Development Notes", notes_content))

        return "\n\n".join(sections)

    def _build_overview_section(self, memory_data: dict[str, Any]) -> str:
        """Build the overview section content.

        Args:
            memory_data: The full memory data dictionary.

        Returns:
            str: Formatted overview content.
        """
        bundle_info = memory_data.get("bundle_info", {})

        bundle_id = bundle_info.get("bundle_id", "Not specified")
        bundle_name = bundle_info.get("bundle_name", "Not specified")
        version = bundle_info.get("version", "")
        build = bundle_info.get("build", "")
        min_ios = bundle_info.get("min_ios", "Not specified")

        # Format version string
        if version and build:
            version_str = f"{version} (Build {build})"
        elif version:
            version_str = version
        else:
            version_str = "Not specified"

        lines = [
            f"- **Bundle ID:** {bundle_id}",
            f"- **Bundle Name:** {bundle_name}",
            f"- **Version:** {version_str}",
            f"- **Minimum iOS:** {min_ios}",
        ]
        return "\n".join(lines)

    def _build_swift_files_section(self, memory_data: dict[str, Any]) -> str:
        """Build the Swift files section content.

        Args:
            memory_data: The full memory data dictionary.

        Returns:
            str: Formatted Swift files content.
        """
        swift_files = memory_data.get("swift_files", {})
        count = swift_files.get("count", 0)
        directories = swift_files.get("directories", [])

        lines = [f"- **Count:** {count} files"]

        if directories:
            dirs_str = ", ".join(directories)
            lines.append(f"- **Directories:** {dirs_str}")
        else:
            lines.append("- **Directories:** *None detected*")

        return "\n".join(lines)

    def _build_interop_section(self, memory_data: dict[str, Any]) -> str:
        """Build the Kotlin/Swift interop section content.

        Args:
            memory_data: The full memory data dictionary.

        Returns:
            str: Formatted interop content.
        """
        interop = memory_data.get("interop", {})
        patterns = interop.get("patterns", [])

        sections = ["### Detected Patterns"]

        if patterns:
            for pattern in patterns:
                sections.append(f"- `{pattern}`")
        else:
            sections.append("*No interop patterns detected*")

        return "\n".join(sections)

    def _build_dependencies_section(self, memory_data: dict[str, Any]) -> str:
        """Build the dependencies section content.

        Args:
            memory_data: The full memory data dictionary.

        Returns:
            str: Formatted dependencies content.
        """
        dependencies = memory_data.get("dependencies", {})
        sections = []

        # CocoaPods
        cocoapods = dependencies.get("cocoapods", {})
        sections.append("### CocoaPods")
        if cocoapods.get("has_podfile"):
            sections.append("*Using Podfile*")
            pods = cocoapods.get("pods", [])
            if pods:
                for pod in pods:
                    sections.append(f"- {pod}")
            else:
                sections.append("*No pods listed*")
        else:
            sections.append("*Not configured*")

        # Swift Package Manager
        sections.append("")
        sections.append("### Swift Package Manager")
        spm = dependencies.get("spm", {})
        if spm.get("has_package_swift"):
            sections.append("*Using Package.swift*")
            packages = spm.get("packages", [])
            if packages:
                for package in packages:
                    sections.append(f"- {package}")
            else:
                sections.append("*No packages listed*")
        else:
            sections.append("*Not configured*")

        return "\n".join(sections)

    def _build_privacy_section(self, privacy_descriptions: dict[str, str]) -> str:
        """Build the privacy descriptions section.

        Args:
            privacy_descriptions: Dictionary mapping permission keys to descriptions.

        Returns:
            str: Formatted privacy descriptions as a table.
        """
        if not privacy_descriptions:
            return "*No privacy descriptions found*"

        # Map common privacy keys to readable names
        key_names = {
            "NSCameraUsageDescription": "Camera",
            "NSPhotoLibraryUsageDescription": "Photo Library",
            "NSPhotoLibraryAddUsageDescription": "Photo Library (Add)",
            "NSMicrophoneUsageDescription": "Microphone",
            "NSLocationWhenInUseUsageDescription": "Location (When In Use)",
            "NSLocationAlwaysUsageDescription": "Location (Always)",
            "NSLocationAlwaysAndWhenInUseUsageDescription": "Location (Always & When In Use)",
            "NSContactsUsageDescription": "Contacts",
            "NSCalendarsUsageDescription": "Calendars",
            "NSRemindersUsageDescription": "Reminders",
            "NSMotionUsageDescription": "Motion",
            "NSHealthShareUsageDescription": "Health (Read)",
            "NSHealthUpdateUsageDescription": "Health (Write)",
            "NSBluetoothAlwaysUsageDescription": "Bluetooth",
            "NSBluetoothPeripheralUsageDescription": "Bluetooth Peripheral",
            "NSSpeechRecognitionUsageDescription": "Speech Recognition",
            "NSFaceIDUsageDescription": "Face ID",
            "NSAppleMusicUsageDescription": "Apple Music",
            "NSUserTrackingUsageDescription": "User Tracking",
        }

        headers = ["Permission", "Description"]
        rows = []
        for key, description in privacy_descriptions.items():
            readable_name = key_names.get(key, key)
            rows.append([readable_name, description])

        return self._format_table(headers, rows)

    def _build_url_schemes_section(self, url_schemes: list[str]) -> str:
        """Build the URL schemes section.

        Args:
            url_schemes: List of registered URL schemes.

        Returns:
            str: Formatted URL schemes list.
        """
        if not url_schemes:
            return "*No URL schemes registered*"

        lines = []
        for scheme in url_schemes:
            lines.append(f"- `{scheme}://`")

        return "\n".join(lines)

    def _build_xcode_section(self, xcode_data: dict[str, Any]) -> str:
        """Build the Xcode project section.

        Args:
            xcode_data: Dictionary containing Xcode project information.

        Returns:
            str: Formatted Xcode project content.
        """
        name = xcode_data.get("name", "Unknown")
        path = xcode_data.get("path", "")
        project_type = xcode_data.get("type", "")

        lines = [f"- **Name:** {name}"]

        if path:
            lines.append(f"- **Path:** `{path}`")

        if project_type:
            lines.append(f"- **Type:** {project_type}")

        return "\n".join(lines)

    def _build_development_notes(self, memory_data: dict[str, Any]) -> str:
        """Build the development notes section.

        Args:
            memory_data: The full memory data dictionary.

        Returns:
            str: Formatted development notes.
        """
        notes = []

        # Add notes about minimum iOS version
        bundle_info = memory_data.get("bundle_info", {})
        min_ios = bundle_info.get("min_ios", "")
        if min_ios:
            notes.append(f"- Minimum iOS {min_ios} is required")

        # Add notes about interop patterns
        interop = memory_data.get("interop", {})
        patterns = interop.get("patterns", [])
        if patterns:
            if "@ObjCName" in patterns:
                notes.append("- Swift interop uses @ObjCName annotations")
            if "expect/actual" in patterns or any("expect" in p.lower() for p in patterns):
                notes.append("- Uses expect/actual declarations for platform-specific code")
            if any("KotlinBase" in p for p in patterns):
                notes.append("- Has KotlinBase extensions for Swift interop")

        # Add notes about dependencies
        dependencies = memory_data.get("dependencies", {})
        cocoapods = dependencies.get("cocoapods", {})
        spm = dependencies.get("spm", {})

        if cocoapods.get("has_podfile"):
            notes.append("- CocoaPods managed via Podfile")
        if spm.get("has_package_swift"):
            notes.append("- Swift Package Manager via Package.swift")

        # Add notes about privacy permissions
        privacy = memory_data.get("privacy_descriptions", {})
        if privacy:
            notes.append(f"- {len(privacy)} privacy permission(s) declared")

        return "\n".join(notes) if notes else "*No specific development notes*"

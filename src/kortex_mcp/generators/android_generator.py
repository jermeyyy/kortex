"""Generator for Android platform memory content.

This module provides the AndroidMemoryGenerator class for transforming
Android-specific analysis data into structured memory content.
"""

from typing import Any

from kortex_mcp.generators.base import BaseMemoryGenerator


class AndroidMemoryGenerator(BaseMemoryGenerator):
    """Generator for Android platform memories.

    This generator transforms raw Android analysis data into a
    comprehensive memory document that describes the Android configuration,
    including:
    - SDK versions (min, target, compile)
    - Build configuration (build types, product flavors)
    - AndroidManifest contents (permissions, components)
    - Resource overview
    - ProGuard/R8 configuration

    The generated memory helps AI agents understand the Android-specific
    configuration and make informed decisions about platform features.

    Example:
        >>> generator = AndroidMemoryGenerator()
        >>> analysis_data = {
        ...     "application_id": "com.example.app",
        ...     "min_sdk": 24,
        ...     "target_sdk": 34,
        ...     "compile_sdk": 34,
        ...     "build_types": [
        ...         {"name": "debug", "minify_enabled": False, "debuggable": True},
        ...         {"name": "release", "minify_enabled": True, "debuggable": False},
        ...     ],
        ...     "permissions": ["android.permission.INTERNET"],
        ... }
        >>> content = generator.generate_content(analysis_data)
        >>> markdown = generator.to_markdown(content)
    """

    @property
    def memory_id(self) -> str:
        """Unique identifier for Android platform memories.

        Returns:
            str: The identifier "android_platform".
        """
        return "android_platform"

    @property
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        Returns:
            str: The title "Android Platform".
        """
        return "Android Platform"

    @property
    def memory_category(self) -> str:
        """Category for organizing Android platform memories.

        Returns:
            str: The category "android_platform".
        """
        return "android_platform"

    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from Android analysis data.

        Transforms raw Android analysis results into a normalized
        dictionary containing platform configuration information.

        Args:
            analysis_data: Dictionary containing Android analysis results.
                Expected structure:
                {
                    "application_id": "com.example.app",
                    "min_sdk": 24,
                    "target_sdk": 34,
                    "compile_sdk": 34,
                    "build_types": [
                        {"name": "debug", "minify_enabled": False, "debuggable": True},
                        ...
                    ],
                    "product_flavors": [...],
                    "manifest": {
                        "package": "com.example.app",
                        "permissions": [...],
                        "activities": [...],
                        "services": [...],
                        ...
                    },
                    "resources": {"drawable": 45, "layout": 23, ...},
                    "proguard": {"enabled": True, "files": ["proguard-rules.pro"]}
                }

        Returns:
            dict[str, Any]: Structured memory content with keys:
                - application_id: Application identifier
                - min_sdk: Minimum SDK version
                - target_sdk: Target SDK version
                - compile_sdk: Compile SDK version
                - build_types: List of build type configurations
                - product_flavors: List of product flavors
                - manifest: AndroidManifest information
                - resources: Resource counts by type
                - proguard: ProGuard/R8 configuration

        Raises:
            ValueError: If analysis_data is None.
        """
        if analysis_data is None:
            raise ValueError("Analysis data cannot be None")

        # Extract and normalize SDK versions
        min_sdk = analysis_data.get("min_sdk", 21)
        target_sdk = analysis_data.get("target_sdk", 34)
        compile_sdk = analysis_data.get("compile_sdk", target_sdk)

        # Normalize build types
        build_types = []
        for bt in analysis_data.get("build_types", []):
            if isinstance(bt, dict):
                build_types.append({
                    "name": bt.get("name", "unknown"),
                    "minify_enabled": bt.get("minify_enabled", False),
                    "debuggable": bt.get("debuggable", False),
                })

        # Normalize product flavors
        product_flavors = []
        for pf in analysis_data.get("product_flavors", []):
            if isinstance(pf, dict):
                product_flavors.append({
                    "name": pf.get("name", "unknown"),
                    "dimension": pf.get("dimension", ""),
                    "application_id_suffix": pf.get("application_id_suffix", ""),
                })

        # Normalize manifest data
        manifest_data = analysis_data.get("manifest", {})
        manifest = {
            "package": manifest_data.get("package", analysis_data.get("application_id", "")),
            "permissions": manifest_data.get("permissions", analysis_data.get("permissions", [])),
            "activities": manifest_data.get("activities", []),
            "services": manifest_data.get("services", []),
            "receivers": manifest_data.get("receivers", []),
            "providers": manifest_data.get("providers", []),
        }

        # Normalize resources
        resources = analysis_data.get("resources", {})

        # Normalize ProGuard configuration
        proguard_data = analysis_data.get("proguard", {})
        proguard = {
            "enabled": proguard_data.get("enabled", False),
            "files": proguard_data.get("files", []),
        }

        return {
            "application_id": analysis_data.get("application_id", ""),
            "min_sdk": min_sdk,
            "target_sdk": target_sdk,
            "compile_sdk": compile_sdk,
            "build_types": build_types,
            "product_flavors": product_flavors,
            "manifest": manifest,
            "resources": resources,
            "proguard": proguard,
        }

    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        Creates a well-formatted markdown document describing the Android
        platform configuration, suitable for consumption by AI agents.

        Args:
            memory_data: Structured memory content as returned by generate_content.
                Expected keys: application_id, min_sdk, target_sdk, compile_sdk,
                build_types, product_flavors, manifest, resources, proguard.

        Returns:
            str: Markdown-formatted string representation of the Android config.

        Raises:
            ValueError: If memory_data is None or missing required fields.
        """
        if not memory_data:
            raise ValueError("Memory data cannot be empty")

        sections = []

        # Main title
        sections.append("# Android Platform Configuration")

        # Overview section
        overview_content = self._build_overview_section(memory_data)
        sections.append(self._format_section("Overview", overview_content))

        # Build configuration section
        build_config_content = self._build_configuration_section(memory_data)
        sections.append(self._format_section("Build Configuration", build_config_content))

        # AndroidManifest section
        manifest_content = self._build_manifest_section(memory_data.get("manifest", {}))
        sections.append(self._format_section("AndroidManifest", manifest_content))

        # Resources section
        resources = memory_data.get("resources", {})
        if resources:
            resources_content = self._build_resources_section(resources)
            sections.append(self._format_section("Resources", resources_content))

        # ProGuard/R8 section
        proguard = memory_data.get("proguard", {})
        proguard_content = self._build_proguard_section(proguard)
        sections.append(self._format_section("ProGuard/R8", proguard_content))

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
        app_id = memory_data.get("application_id", "Not specified")
        min_sdk = memory_data.get("min_sdk", 21)
        target_sdk = memory_data.get("target_sdk", 34)
        compile_sdk = memory_data.get("compile_sdk", 34)

        lines = [
            f"- **Application ID:** {app_id}",
            f"- **Min SDK:** {min_sdk} ({self._get_android_version_name(min_sdk)})",
            f"- **Target SDK:** {target_sdk} ({self._get_android_version_name(target_sdk)})",
            f"- **Compile SDK:** {compile_sdk}",
        ]
        return "\n".join(lines)

    def _build_configuration_section(self, memory_data: dict[str, Any]) -> str:
        """Build the build configuration section.

        Args:
            memory_data: The full memory data dictionary.

        Returns:
            str: Formatted build configuration content.
        """
        sections = []

        # Build types table
        build_types = memory_data.get("build_types", [])
        if build_types:
            headers = ["Type", "Minify", "Debug"]
            rows = []
            for bt in build_types:
                rows.append([
                    bt.get("name", "unknown"),
                    "Yes" if bt.get("minify_enabled") else "No",
                    "Yes" if bt.get("debuggable") else "No",
                ])
            sections.append("### Build Types")
            sections.append(self._format_table(headers, rows))
        else:
            sections.append("### Build Types")
            sections.append("*No build types configured*")

        # Product flavors
        product_flavors = memory_data.get("product_flavors", [])
        sections.append("")
        sections.append("### Product Flavors")
        if product_flavors:
            headers = ["Name", "Dimension", "App ID Suffix"]
            rows = []
            for pf in product_flavors:
                rows.append([
                    pf.get("name", "unknown"),
                    pf.get("dimension", "-"),
                    pf.get("application_id_suffix", "-") or "-",
                ])
            sections.append(self._format_table(headers, rows))
        else:
            sections.append("*No product flavors configured*")

        return "\n".join(sections)

    def _build_manifest_section(self, manifest: dict[str, Any]) -> str:
        """Build the AndroidManifest section.

        Args:
            manifest: The manifest data dictionary.

        Returns:
            str: Formatted manifest content.
        """
        sections = []

        # Package
        package = manifest.get("package", "")
        if package:
            sections.append("### Package")
            sections.append(f"`{package}`")

        # Permissions
        permissions = manifest.get("permissions", [])
        sections.append("")
        sections.append("### Permissions")
        if permissions:
            for perm in permissions:
                sections.append(f"- `{perm}`")
        else:
            sections.append("*No permissions declared*")

        # Components section
        sections.append("")
        sections.append("### Components")

        # Activities
        activities = manifest.get("activities", [])
        sections.append("#### Activities")
        if activities:
            headers = ["Activity", "Exported"]
            rows = []
            for activity in activities:
                if isinstance(activity, dict):
                    name = activity.get("name", "unknown")
                    exported = "Yes" if activity.get("exported") else "No"
                else:
                    name = str(activity)
                    exported = "-"
                rows.append([name, exported])
            sections.append(self._format_table(headers, rows))
        else:
            sections.append("*No activities declared*")

        # Services
        services = manifest.get("services", [])
        sections.append("")
        sections.append("#### Services")
        if services:
            headers = ["Service", "Exported"]
            rows = []
            for service in services:
                if isinstance(service, dict):
                    name = service.get("name", "unknown")
                    exported = "Yes" if service.get("exported") else "No"
                else:
                    name = str(service)
                    exported = "-"
                rows.append([name, exported])
            sections.append(self._format_table(headers, rows))
        else:
            sections.append("*No services declared*")

        # Broadcast Receivers
        receivers = manifest.get("receivers", [])
        if receivers:
            sections.append("")
            sections.append("#### Broadcast Receivers")
            headers = ["Receiver", "Exported"]
            rows = []
            for receiver in receivers:
                if isinstance(receiver, dict):
                    name = receiver.get("name", "unknown")
                    exported = "Yes" if receiver.get("exported") else "No"
                else:
                    name = str(receiver)
                    exported = "-"
                rows.append([name, exported])
            sections.append(self._format_table(headers, rows))

        # Content Providers
        providers = manifest.get("providers", [])
        if providers:
            sections.append("")
            sections.append("#### Content Providers")
            headers = ["Provider", "Exported"]
            rows = []
            for provider in providers:
                if isinstance(provider, dict):
                    name = provider.get("name", "unknown")
                    exported = "Yes" if provider.get("exported") else "No"
                else:
                    name = str(provider)
                    exported = "-"
                rows.append([name, exported])
            sections.append(self._format_table(headers, rows))

        return "\n".join(sections)

    def _build_resources_section(self, resources: dict[str, Any]) -> str:
        """Build the resources section.

        Args:
            resources: Dictionary mapping resource types to counts.

        Returns:
            str: Formatted resources content.
        """
        if not resources:
            return "*No resource information available*"

        headers = ["Type", "Count"]
        rows = []
        for resource_type, count in sorted(resources.items()):
            rows.append([resource_type, str(count)])

        return self._format_table(headers, rows)

    def _build_proguard_section(self, proguard: dict[str, Any]) -> str:
        """Build the ProGuard/R8 section.

        Args:
            proguard: Dictionary containing ProGuard configuration.

        Returns:
            str: Formatted ProGuard content.
        """
        enabled = proguard.get("enabled", False)
        files = proguard.get("files", [])

        lines = [
            f"- **Enabled:** {'Yes' if enabled else 'No'}",
        ]

        if files:
            files_str = ", ".join(f"`{f}`" for f in files)
            lines.append(f"- **Files:** {files_str}")

        return "\n".join(lines)

    def _build_development_notes(self, memory_data: dict[str, Any]) -> str:
        """Build the development notes section.

        Args:
            memory_data: The full memory data dictionary.

        Returns:
            str: Formatted development notes.
        """
        notes = []
        target_sdk = memory_data.get("target_sdk", 34)

        notes.append(f"- Target API {target_sdk} for latest features")

        # Add notes about permissions
        manifest = memory_data.get("manifest", {})
        permissions = manifest.get("permissions", [])

        notable_permissions = {
            "android.permission.CAMERA": "Camera permission required",
            "android.permission.INTERNET": "Network access enabled",
            "android.permission.ACCESS_FINE_LOCATION": "Fine location access required",
            "android.permission.ACCESS_COARSE_LOCATION": "Coarse location access required",
            "android.permission.RECORD_AUDIO": "Audio recording enabled",
            "android.permission.READ_EXTERNAL_STORAGE": "External storage read access",
            "android.permission.WRITE_EXTERNAL_STORAGE": "External storage write access",
        }

        for perm in permissions:
            if perm in notable_permissions:
                notes.append(f"- {notable_permissions[perm]}")

        # Add notes about min SDK
        min_sdk = memory_data.get("min_sdk", 21)
        if min_sdk < 24:
            notes.append("- Consider updating min SDK to 24+ for better API coverage")

        return "\n".join(notes) if notes else "*No specific development notes*"

    def _get_android_version_name(self, sdk_version: int) -> str:
        """Get the Android version name for an SDK version.

        Args:
            sdk_version: The Android SDK version number.

        Returns:
            str: Human-readable Android version name.
        """
        version_names = {
            21: "Android 5.0",
            22: "Android 5.1",
            23: "Android 6.0",
            24: "Android 7.0",
            25: "Android 7.1",
            26: "Android 8.0",
            27: "Android 8.1",
            28: "Android 9",
            29: "Android 10",
            30: "Android 11",
            31: "Android 12",
            32: "Android 12L",
            33: "Android 13",
            34: "Android 14",
            35: "Android 15",
        }
        return version_names.get(sdk_version, f"Android SDK {sdk_version}")

"""Android platform analyzer for KMP/CMP projects.

This module provides the AndroidAnalyzer class for analyzing Android-specific
configuration, resources, and build settings in Kotlin Multiplatform projects.
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .base import AnalysisResult, BaseAnalyzer

logger = logging.getLogger(__name__)


class AndroidAnalyzer(BaseAnalyzer):
    """Analyzer for Android platform configuration in KMP/CMP projects.

    Analyzes Android-specific aspects of Kotlin Multiplatform projects:
    - AndroidManifest.xml files (permissions, components, metadata)
    - Build configuration (SDK versions, build types, flavors)
    - Resource structure (drawables, layouts, values)
    - ProGuard/R8 configuration

    This analyzer helps understand the Android target configuration
    and resources in a multiplatform project.

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> analyzer = AndroidAnalyzer(Path("/path/to/kmp-project"))
        >>> result = await analyzer.analyze()
        >>> print(result.data["manifests"])
        [{"path": "src/androidMain/AndroidManifest.xml", ...}]
        >>> print(result.data["build_config"]["minSdk"])
        24
    """

    # Regex patterns for parsing build.gradle.kts
    NAMESPACE_PATTERN = re.compile(
        r'namespace\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    APPLICATION_ID_PATTERN = re.compile(
        r'applicationId\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    MIN_SDK_PATTERN = re.compile(
        r'minSdk\s*=\s*(\d+)',
        re.MULTILINE
    )

    TARGET_SDK_PATTERN = re.compile(
        r'targetSdk\s*=\s*(\d+)',
        re.MULTILINE
    )

    COMPILE_SDK_PATTERN = re.compile(
        r'compileSdk\s*=\s*(\d+)',
        re.MULTILINE
    )

    # Build type detection pattern
    BUILD_TYPE_PATTERN = re.compile(
        r'buildTypes\s*\{[^}]*(?:getByName|create)\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE | re.DOTALL
    )

    # Product flavor detection pattern
    PRODUCT_FLAVOR_PATTERN = re.compile(
        r'productFlavors\s*\{[^}]*(?:create)\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE | re.DOTALL
    )

    # Signing config detection pattern
    SIGNING_CONFIG_PATTERN = re.compile(
        r'signingConfigs\s*\{[^}]*(?:create|getByName)\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE | re.DOTALL
    )

    # Minification enabled pattern
    MINIFY_ENABLED_PATTERN = re.compile(
        r'isMinifyEnabled\s*=\s*(true|false)',
        re.MULTILINE
    )

    @property
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            Human-readable name identifying this analyzer.
        """
        return "android"

    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            String identifier for the category under which analysis
            results should be stored in the memory system.
        """
        return "android_platform"

    def _extract_block(self, content: str, block_name: str) -> str | None:
        """Extract a block's content using brace matching.

        Args:
            content: Full file content.
            block_name: Name of the block to extract (e.g., "buildTypes").

        Returns:
            Content inside the block's braces, or None if not found.
        """
        # Find the start of the block
        pattern = rf'{block_name}\s*\{{'
        match = re.search(pattern, content)
        if not match:
            return None

        start_pos = match.end() - 1  # Position of opening brace
        brace_count = 0
        block_start = start_pos + 1
        block_end = start_pos

        for i in range(start_pos, len(content)):
            char = content[i]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    block_end = i
                    break

        if block_end > block_start:
            return content[block_start:block_end]
        return None

    async def analyze(self) -> AnalysisResult:
        """Analyze Android platform configuration in the project.

        Scans for AndroidManifest.xml files, parses build.gradle.kts
        for Android configuration, analyzes resource directories,
        and checks for ProGuard/R8 configuration.

        Returns:
            AnalysisResult containing:
            {
                "manifests": [...],
                "build_config": {...},
                "resources": {...},
                "proguard": {...}
            }

        Example:
            >>> result = await analyzer.analyze()
            >>> print(result.data["build_config"]["minSdk"])
            24
        """
        try:
            logger.info(f"Analyzing Android configuration for project: {self.project_root}")
            warnings: list[str] = []

            # Check if project has Android target
            has_android = self._detect_android_target()
            if not has_android:
                logger.warning("No Android target detected in project")
                warnings.append("No Android target detected in this project")
                return AnalysisResult(
                    analyzer_name=self.name,
                    success=True,
                    data={
                        "manifests": [],
                        "build_config": {},
                        "resources": {},
                        "proguard": {"enabled": False, "files": []},
                    },
                    errors=[],
                    warnings=warnings,
                )

            # Parse AndroidManifest.xml files
            manifests = self._parse_manifests()
            logger.debug(f"Found {len(manifests)} AndroidManifest.xml files")

            # Parse build configuration
            build_config = self._parse_build_config()
            logger.debug(f"Parsed build config: minSdk={build_config.get('minSdk')}")

            # Analyze resource structure
            resources = self._analyze_resources()
            logger.debug(f"Found resources in {len(resources)} categories")

            # Check ProGuard/R8 configuration
            proguard = self._analyze_proguard()
            logger.debug(f"ProGuard enabled: {proguard.get('enabled')}")

            data = {
                "manifests": manifests,
                "build_config": build_config,
                "resources": resources,
                "proguard": proguard,
            }

            logger.info(
                f"Android analysis complete. Found {len(manifests)} manifests, "
                f"minSdk={build_config.get('minSdk')}"
            )

            result = self._create_success_result(data)
            result.warnings = warnings
            return result

        except Exception as e:
            logger.error(f"Error analyzing Android configuration: {e}")
            return self._create_error_result(
                errors=[f"Failed to analyze Android configuration: {str(e)}"]
            )

    def _detect_android_target(self) -> bool:
        """Detect if the project has an Android target.

        Checks for androidMain source set or android block in build files.

        Returns:
            True if Android target is detected.
        """
        # Check for androidMain source set
        android_main = self.project_root / "src" / "androidMain"
        if android_main.exists():
            return True

        # Check build.gradle.kts files for android block
        build_files = list(self.project_root.rglob("build.gradle.kts"))
        build_files.extend(list(self.project_root.rglob("build.gradle")))

        for build_file in build_files:
            try:
                content = build_file.read_text(encoding="utf-8")
                if "android {" in content or "android{" in content:
                    return True
                if "androidTarget()" in content:
                    return True
                if 'id("com.android' in content or "id('com.android" in content:
                    return True
            except Exception as e:
                logger.warning(f"Error reading {build_file}: {e}")

        return False

    def _parse_manifests(self) -> list[dict[str, Any]]:
        """Parse all AndroidManifest.xml files in the project.

        Returns:
            List of manifest data dictionaries containing:
            - path: relative path to manifest
            - package: package name
            - permissions: list of permissions
            - features: list of required features
            - components: activities, services, receivers, providers
            - metadata: application metadata
        """
        manifests: list[dict[str, Any]] = []

        # Find all AndroidManifest.xml files
        manifest_files = list(self.project_root.rglob("AndroidManifest.xml"))

        for manifest_file in manifest_files:
            try:
                manifest_data = self._parse_single_manifest(manifest_file)
                if manifest_data:
                    manifests.append(manifest_data)
            except Exception as e:
                logger.warning(f"Error parsing manifest {manifest_file}: {e}")

        return manifests

    def _parse_single_manifest(self, manifest_path: Path) -> dict[str, Any] | None:
        """Parse a single AndroidManifest.xml file.

        Args:
            manifest_path: Path to the manifest file.

        Returns:
            Dictionary with manifest data or None if parsing fails.
        """
        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()

            # Android XML namespace
            android_ns = "{http://schemas.android.com/apk/res/android}"

            # Extract package name
            package = root.get("package", "")

            # Extract permissions
            permissions: list[str] = []
            for perm in root.findall("uses-permission"):
                perm_name = perm.get(f"{android_ns}name", "")
                if perm_name:
                    # Extract just the permission name without prefix
                    short_name = perm_name.split(".")[-1]
                    permissions.append(short_name)

            # Extract features
            features: list[str] = []
            for feature in root.findall("uses-feature"):
                feature_name = feature.get(f"{android_ns}name", "")
                if feature_name:
                    features.append(feature_name)

            # Extract components
            components = self._extract_components(root, android_ns)

            # Extract application metadata
            metadata = self._extract_metadata(root, android_ns)

            return {
                "path": str(manifest_path.relative_to(self.project_root)),
                "package": package,
                "permissions": permissions,
                "features": features,
                "components": components,
                "metadata": metadata,
            }

        except ET.ParseError as e:
            logger.warning(f"XML parse error in {manifest_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error reading manifest {manifest_path}: {e}")
            return None

    def _extract_components(
        self,
        root: ET.Element,
        android_ns: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Extract Android components from manifest.

        Args:
            root: XML root element.
            android_ns: Android namespace prefix.

        Returns:
            Dictionary with activities, services, receivers, providers.
        """
        components: dict[str, list[dict[str, Any]]] = {
            "activities": [],
            "services": [],
            "receivers": [],
            "providers": [],
        }

        # Find application element
        application = root.find("application")
        if application is None:
            return components

        # Extract activities
        for activity in application.findall("activity"):
            activity_data = self._extract_component_data(activity, android_ns)
            if activity_data:
                components["activities"].append(activity_data)

        # Extract activity-alias
        for activity_alias in application.findall("activity-alias"):
            alias_data = self._extract_component_data(activity_alias, android_ns)
            if alias_data:
                alias_data["is_alias"] = True
                components["activities"].append(alias_data)

        # Extract services
        for service in application.findall("service"):
            service_data = self._extract_component_data(service, android_ns)
            if service_data:
                components["services"].append(service_data)

        # Extract receivers
        for receiver in application.findall("receiver"):
            receiver_data = self._extract_component_data(receiver, android_ns)
            if receiver_data:
                components["receivers"].append(receiver_data)

        # Extract providers
        for provider in application.findall("provider"):
            provider_data = self._extract_component_data(provider, android_ns)
            if provider_data:
                # Add provider-specific attributes
                authorities = provider.get(f"{android_ns}authorities", "")
                if authorities:
                    provider_data["authorities"] = authorities
                components["providers"].append(provider_data)

        return components

    def _extract_component_data(
        self,
        element: ET.Element,
        android_ns: str
    ) -> dict[str, Any] | None:
        """Extract common component data from XML element.

        Args:
            element: XML element representing a component.
            android_ns: Android namespace prefix.

        Returns:
            Dictionary with component data or None.
        """
        name = element.get(f"{android_ns}name", "")
        if not name:
            return None

        data: dict[str, Any] = {"name": name}

        # Extract common attributes
        exported = element.get(f"{android_ns}exported")
        if exported is not None:
            data["exported"] = exported.lower() == "true"

        enabled = element.get(f"{android_ns}enabled")
        if enabled is not None:
            data["enabled"] = enabled.lower() == "true"

        # Extract intent filters
        intent_filters: list[dict[str, Any]] = []
        for intent_filter in element.findall("intent-filter"):
            filter_data = self._extract_intent_filter(intent_filter, android_ns)
            if filter_data:
                intent_filters.append(filter_data)

        if intent_filters:
            data["intent_filters"] = intent_filters

        return data

    def _extract_intent_filter(
        self,
        element: ET.Element,
        android_ns: str
    ) -> dict[str, Any]:
        """Extract intent filter data.

        Args:
            element: Intent filter XML element.
            android_ns: Android namespace prefix.

        Returns:
            Dictionary with actions, categories, and data elements.
        """
        actions: list[str] = []
        categories: list[str] = []
        data_elements: list[dict[str, str]] = []

        for action in element.findall("action"):
            action_name = action.get(f"{android_ns}name", "")
            if action_name:
                actions.append(action_name)

        for category in element.findall("category"):
            category_name = category.get(f"{android_ns}name", "")
            if category_name:
                categories.append(category_name)

        for data in element.findall("data"):
            data_dict: dict[str, str] = {}
            for attr in ["scheme", "host", "port", "path", "pathPrefix", "mimeType"]:
                value = data.get(f"{android_ns}{attr}", "")
                if value:
                    data_dict[attr] = value
            if data_dict:
                data_elements.append(data_dict)

        return {
            "actions": actions,
            "categories": categories,
            "data": data_elements,
        }

    def _extract_metadata(
        self,
        root: ET.Element,
        android_ns: str
    ) -> dict[str, str]:
        """Extract application metadata from manifest.

        Args:
            root: XML root element.
            android_ns: Android namespace prefix.

        Returns:
            Dictionary of metadata name to value.
        """
        metadata: dict[str, str] = {}

        application = root.find("application")
        if application is None:
            return metadata

        for meta in application.findall("meta-data"):
            name = meta.get(f"{android_ns}name", "")
            value = meta.get(f"{android_ns}value", "")
            resource = meta.get(f"{android_ns}resource", "")

            if name:
                metadata[name] = value or resource

        return metadata

    def _parse_build_config(self) -> dict[str, Any]:
        """Parse Android build configuration from build.gradle.kts files.

        Returns:
            Dictionary containing:
            - applicationId: Application ID
            - minSdk: Minimum SDK version
            - targetSdk: Target SDK version
            - compileSdk: Compile SDK version
            - build_types: List of build type names
            - flavors: List of product flavor configurations
            - signing: Signing configuration info
        """
        build_config: dict[str, Any] = {
            "applicationId": None,
            "minSdk": None,
            "targetSdk": None,
            "compileSdk": None,
            "build_types": [],
            "flavors": [],
            "signing": {},
        }

        # Find build.gradle.kts files
        build_files = list(self.project_root.rglob("build.gradle.kts"))
        build_files.extend(list(self.project_root.rglob("build.gradle")))

        for build_file in build_files:
            try:
                content = build_file.read_text(encoding="utf-8")

                # Only process files with android block
                if "android {" not in content and "android{" not in content:
                    continue

                # Parse namespace (used as applicationId in library modules)
                match = self.NAMESPACE_PATTERN.search(content)
                if match and not build_config["applicationId"]:
                    build_config["applicationId"] = match.group(1)

                # Parse applicationId
                match = self.APPLICATION_ID_PATTERN.search(content)
                if match:
                    build_config["applicationId"] = match.group(1)

                # Parse SDK versions
                match = self.MIN_SDK_PATTERN.search(content)
                if match:
                    build_config["minSdk"] = int(match.group(1))

                match = self.TARGET_SDK_PATTERN.search(content)
                if match:
                    build_config["targetSdk"] = int(match.group(1))

                match = self.COMPILE_SDK_PATTERN.search(content)
                if match:
                    build_config["compileSdk"] = int(match.group(1))

                # Parse build types
                build_types = self._extract_build_types(content)
                for bt in build_types:
                    if bt not in build_config["build_types"]:
                        build_config["build_types"].append(bt)

                # Parse product flavors
                flavors = self._extract_product_flavors(content)
                build_config["flavors"].extend(flavors)

                # Parse signing configs
                signing = self._extract_signing_configs(content)
                if signing:
                    build_config["signing"] = signing

            except Exception as e:
                logger.warning(f"Error parsing build config from {build_file}: {e}")

        # Add default build types if none found
        if not build_config["build_types"]:
            build_config["build_types"] = ["debug", "release"]

        return build_config

    def _extract_build_types(self, content: str) -> list[str]:
        """Extract build type names from build file content.

        Args:
            content: Build file content.

        Returns:
            List of build type names.
        """
        build_types: list[str] = []

        # Find buildTypes block using brace matching
        block = self._extract_block(content, "buildTypes")

        if block:
            # Find getByName or create calls
            for match in re.finditer(
                r'(?:getByName|create)\s*\(\s*["\'](\w+)["\']',
                block
            ):
                bt_name = match.group(1)
                if bt_name not in build_types:
                    build_types.append(bt_name)

            # Also check for direct named blocks (Kotlin DSL)
            for match in re.finditer(r'(\w+)\s*\{', block):
                bt_name = match.group(1)
                if bt_name in ["debug", "release"] and bt_name not in build_types:
                    build_types.append(bt_name)

        return build_types

    def _extract_product_flavors(self, content: str) -> list[dict[str, Any]]:
        """Extract product flavor configurations from build file.

        Args:
            content: Build file content.

        Returns:
            List of product flavor dictionaries.
        """
        flavors: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        # Find productFlavors block using brace matching
        block = self._extract_block(content, "productFlavors")

        if block:
            # Find flavor names via create or getByName
            for match in re.finditer(
                r'(?:create|getByName)\s*\(\s*["\'](\w+)["\']',
                block
            ):
                flavor_name = match.group(1)
                if flavor_name in seen_names:
                    continue
                seen_names.add(flavor_name)

                flavor_data: dict[str, Any] = {"name": flavor_name}

                # Try to extract dimension from the flavor's block
                flavor_block = self._extract_block(block, flavor_name)
                if flavor_block:
                    dimension_match = re.search(
                        r'dimension\s*=\s*["\'](\w+)["\']',
                        flavor_block
                    )
                    if dimension_match:
                        flavor_data["dimension"] = dimension_match.group(1)

                flavors.append(flavor_data)

        return flavors

    def _extract_signing_configs(self, content: str) -> dict[str, Any]:
        """Extract signing configuration from build file.

        Args:
            content: Build file content.

        Returns:
            Dictionary with signing configuration names.
        """
        signing: dict[str, Any] = {"configs": []}

        # Find signingConfigs block using brace matching
        block = self._extract_block(content, "signingConfigs")

        if block:
            # Find config names
            for match in re.finditer(
                r'(?:create|getByName)\s*\(\s*["\'](\w+)["\']',
                block
            ):
                config_name = match.group(1)
                if config_name not in signing["configs"]:
                    signing["configs"].append(config_name)

        return signing if signing["configs"] else {}

    def _analyze_resources(self) -> dict[str, int]:
        """Analyze Android resource structure.

        Counts resources in res/ directories by type.

        Returns:
            Dictionary mapping resource type to count.
        """
        resources: dict[str, int] = {}

        # Find all res/ directories
        res_dirs: list[Path] = []

        # Check common locations
        possible_res_dirs = [
            self.project_root / "src" / "androidMain" / "res",
            self.project_root / "src" / "main" / "res",
            self.project_root / "app" / "src" / "main" / "res",
        ]

        for res_dir in possible_res_dirs:
            if res_dir.exists():
                res_dirs.append(res_dir)

        # Also search recursively for res directories
        for res_dir in self.project_root.rglob("res"):
            if res_dir.is_dir() and res_dir not in res_dirs:
                # Check if it looks like an Android res directory
                if self._is_android_res_dir(res_dir):
                    res_dirs.append(res_dir)

        # Count resources by type
        for res_dir in res_dirs:
            for subdir in res_dir.iterdir():
                if subdir.is_dir():
                    # Extract resource type (e.g., "drawable" from "drawable-hdpi")
                    res_type = subdir.name.split("-")[0]

                    # Count files in this directory
                    file_count = sum(
                        1 for f in subdir.iterdir()
                        if f.is_file() and not f.name.startswith(".")
                    )

                    if res_type in resources:
                        resources[res_type] += file_count
                    else:
                        resources[res_type] = file_count

        return resources

    def _is_android_res_dir(self, res_dir: Path) -> bool:
        """Check if a directory looks like an Android res directory.

        Args:
            res_dir: Path to check.

        Returns:
            True if directory contains Android resource subdirectories.
        """
        android_res_types = {
            "drawable", "layout", "values", "mipmap", "raw", "xml",
            "anim", "animator", "color", "menu", "font", "navigation"
        }

        for subdir in res_dir.iterdir():
            if subdir.is_dir():
                # Check base name (without qualifiers like -hdpi)
                base_name = subdir.name.split("-")[0]
                if base_name in android_res_types:
                    return True

        return False

    def _analyze_proguard(self) -> dict[str, Any]:
        """Analyze ProGuard/R8 configuration.

        Returns:
            Dictionary containing:
            - enabled: Whether minification is enabled
            - files: List of ProGuard rule files found
        """
        proguard_config: dict[str, Any] = {
            "enabled": False,
            "files": [],
        }

        # Find ProGuard rule files
        proguard_patterns = [
            "proguard-rules.pro",
            "proguard-rules.txt",
            "proguard.cfg",
            "r8-rules.pro",
            "consumer-rules.pro",
        ]

        for pattern in proguard_patterns:
            for rule_file in self.project_root.rglob(pattern):
                relative_path = str(rule_file.relative_to(self.project_root))
                if relative_path not in proguard_config["files"]:
                    proguard_config["files"].append(relative_path)

        # Check if minification is enabled in build files
        build_files = list(self.project_root.rglob("build.gradle.kts"))
        build_files.extend(list(self.project_root.rglob("build.gradle")))

        for build_file in build_files:
            try:
                content = build_file.read_text(encoding="utf-8")

                # Check for isMinifyEnabled = true
                match = self.MINIFY_ENABLED_PATTERN.search(content)
                if match and match.group(1).lower() == "true":
                    proguard_config["enabled"] = True
                    break

                # Also check for minifyEnabled (Groovy style)
                if re.search(r'minifyEnabled\s+true', content):
                    proguard_config["enabled"] = True
                    break

            except Exception as e:
                logger.warning(f"Error checking minification in {build_file}: {e}")

        return proguard_config

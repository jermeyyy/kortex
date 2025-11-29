"""iOS platform analyzer for KMP/CMP projects.

This module provides the iOSAnalyzer class for analyzing iOS-specific
configuration, Swift files, dependencies, and Xcode project settings
in Kotlin Multiplatform projects.
"""

import logging
import plistlib
import re
from pathlib import Path
from typing import Any

from .base import AnalysisResult, BaseAnalyzer

logger = logging.getLogger(__name__)


class iOSAnalyzer(BaseAnalyzer):
    """Analyzer for iOS platform configuration in KMP/CMP projects.

    Analyzes iOS-specific aspects of Kotlin Multiplatform projects:
    - Info.plist files (bundle info, capabilities, privacy descriptions)
    - Swift files in iosMain/ directory
    - Swift/Kotlin interop patterns
    - CocoaPods and Swift Package Manager dependencies
    - Xcode project configuration

    This analyzer helps understand the iOS target configuration
    and resources in a multiplatform project.

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> analyzer = iOSAnalyzer(Path("/path/to/kmp-project"))
        >>> result = await analyzer.analyze()
        >>> print(result.data["info_plists"])
        [{"path": "iosApp/Info.plist", "bundle_id": "com.example.app", ...}]
        >>> print(result.data["swift_files"]["count"])
        15
    """

    # Privacy description keys in Info.plist
    PRIVACY_DESCRIPTION_KEYS = [
        "NSCameraUsageDescription",
        "NSPhotoLibraryUsageDescription",
        "NSPhotoLibraryAddUsageDescription",
        "NSMicrophoneUsageDescription",
        "NSLocationWhenInUseUsageDescription",
        "NSLocationAlwaysUsageDescription",
        "NSLocationAlwaysAndWhenInUseUsageDescription",
        "NSContactsUsageDescription",
        "NSCalendarsUsageDescription",
        "NSRemindersUsageDescription",
        "NSHealthShareUsageDescription",
        "NSHealthUpdateUsageDescription",
        "NSMotionUsageDescription",
        "NSFaceIDUsageDescription",
        "NSSpeechRecognitionUsageDescription",
        "NSAppleMusicUsageDescription",
        "NSBluetoothAlwaysUsageDescription",
        "NSBluetoothPeripheralUsageDescription",
        "NSHomeKitUsageDescription",
        "NSSiriUsageDescription",
        "NSUserTrackingUsageDescription",
        "NSLocalNetworkUsageDescription",
        "NSNearbyInteractionUsageDescription",
    ]

    # Common capability entitlement keys
    CAPABILITY_KEYS = [
        "com.apple.developer.associated-domains",
        "com.apple.developer.default-data-protection",
        "com.apple.developer.icloud-container-identifiers",
        "com.apple.developer.icloud-services",
        "com.apple.developer.in-app-payments",
        "com.apple.developer.networking.wifi-info",
        "com.apple.developer.nfc.readersession.formats",
        "com.apple.developer.pass-type-identifiers",
        "com.apple.developer.siri",
        "com.apple.developer.team-identifier",
        "com.apple.developer.ubiquity-kvstore-identifier",
        "com.apple.security.application-groups",
        "aps-environment",
        "keychain-access-groups",
    ]

    # Interop patterns to detect Swift/Kotlin interoperability
    INTEROP_PATTERNS = {
        "@ObjCName": re.compile(r'@ObjCName\s*\(', re.MULTILINE),
        "@HiddenFromObjC": re.compile(r'@HiddenFromObjC', re.MULTILINE),
        "expect/actual": re.compile(r'\b(expect|actual)\s+(class|fun|val|var|interface|object)\b', re.MULTILINE),
        "KotlinBase": re.compile(r':\s*KotlinBase\b', re.MULTILINE),
        "@objc": re.compile(r'@objc\b', re.MULTILINE),
        "NSObject": re.compile(r':\s*NSObject\b', re.MULTILINE),
    }

    @property
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            Human-readable name identifying this analyzer.
        """
        return "ios"

    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            String identifier for the category under which analysis
            results should be stored in the memory system.
        """
        return "ios_platform"

    async def analyze(self) -> AnalysisResult:
        """Analyze iOS platform configuration in the project.

        Scans for Info.plist files, analyzes Swift files, checks for
        CocoaPods and SPM dependencies, and detects Xcode project configuration.

        Returns:
            AnalysisResult containing:
            {
                "info_plists": [...],
                "swift_files": {...},
                "dependencies": {...},
                "xcode_project": {...}
            }

        Example:
            >>> result = await analyzer.analyze()
            >>> print(result.data["info_plists"][0]["bundle_id"])
            "com.example.app"
        """
        try:
            logger.info(f"Analyzing iOS configuration for project: {self.project_root}")
            warnings: list[str] = []

            # Check if project has iOS target
            has_ios = self._detect_ios_target()
            if not has_ios:
                logger.warning("No iOS target detected in project")
                warnings.append("No iOS target detected in this project")
                return AnalysisResult(
                    analyzer_name=self.name,
                    success=True,
                    data={
                        "info_plists": [],
                        "swift_files": {
                            "count": 0,
                            "directories": [],
                            "interop_patterns": [],
                        },
                        "dependencies": {
                            "cocoapods": {"has_podfile": False, "pods": []},
                            "spm": {"has_package_swift": False, "packages": []},
                        },
                        "xcode_project": {},
                    },
                    errors=[],
                    warnings=warnings,
                )

            # Parse Info.plist files
            info_plists = self._parse_info_plists()
            logger.debug(f"Found {len(info_plists)} Info.plist files")

            # Analyze Swift files
            swift_files = self._analyze_swift_files()
            logger.debug(f"Found {swift_files['count']} Swift files")

            # Analyze dependencies
            dependencies = self._analyze_dependencies()
            logger.debug(
                f"Dependencies: CocoaPods={dependencies['cocoapods']['has_podfile']}, "
                f"SPM={dependencies['spm']['has_package_swift']}"
            )

            # Detect Xcode project
            xcode_project = self._detect_xcode_project()
            logger.debug(f"Xcode project: {xcode_project.get('name', 'Not found')}")

            data = {
                "info_plists": info_plists,
                "swift_files": swift_files,
                "dependencies": dependencies,
                "xcode_project": xcode_project,
            }

            logger.info(
                f"iOS analysis complete. Found {len(info_plists)} Info.plist files, "
                f"{swift_files['count']} Swift files"
            )

            result = self._create_success_result(data)
            result.warnings = warnings
            return result

        except Exception as e:
            logger.error(f"Error analyzing iOS configuration: {e}")
            return self._create_error_result(
                errors=[f"Failed to analyze iOS configuration: {str(e)}"]
            )

    def _detect_ios_target(self) -> bool:
        """Detect if the project has an iOS target.

        Checks for iosMain source set, iOS-related Gradle configuration,
        Xcode projects, or Info.plist files.

        Returns:
            True if iOS target is detected.
        """
        # Check for iosMain source set
        ios_main = self.project_root / "src" / "iosMain"
        if ios_main.exists():
            return True

        # Check for iosApp directory (common KMP convention)
        ios_app = self.project_root / "iosApp"
        if ios_app.exists():
            return True

        # Check for any .xcodeproj or .xcworkspace
        if list(self.project_root.rglob("*.xcodeproj")):
            return True
        if list(self.project_root.rglob("*.xcworkspace")):
            return True

        # Check build.gradle.kts files for iOS target
        build_files = list(self.project_root.rglob("build.gradle.kts"))
        build_files.extend(list(self.project_root.rglob("build.gradle")))

        for build_file in build_files:
            try:
                content = build_file.read_text(encoding="utf-8")
                if any(pattern in content for pattern in [
                    "iosTarget()",
                    "iosX64()",
                    "iosArm64()",
                    "iosSimulatorArm64()",
                    "ios(",
                    "listOf(iosX64",
                    "listOf(iosArm64",
                ]):
                    return True
            except Exception as e:
                logger.warning(f"Error reading {build_file}: {e}")

        return False

    def _parse_info_plists(self) -> list[dict[str, Any]]:
        """Parse all Info.plist files in the project.

        Returns:
            List of Info.plist data dictionaries containing:
            - path: relative path to Info.plist
            - bundle_id: CFBundleIdentifier
            - bundle_name: CFBundleName
            - version: CFBundleShortVersionString
            - build: CFBundleVersion
            - min_ios_version: MinimumOSVersion or LSMinimumSystemVersion
            - capabilities: list of detected capabilities
            - privacy_descriptions: dict of privacy keys and descriptions
            - url_schemes: list of URL schemes
        """
        info_plists: list[dict[str, Any]] = []

        # Find all Info.plist files
        plist_files = list(self.project_root.rglob("Info.plist"))

        for plist_file in plist_files:
            try:
                plist_data = self._parse_single_info_plist(plist_file)
                if plist_data:
                    info_plists.append(plist_data)
            except Exception as e:
                logger.warning(f"Error parsing Info.plist {plist_file}: {e}")

        return info_plists

    def _parse_single_info_plist(self, plist_path: Path) -> dict[str, Any] | None:
        """Parse a single Info.plist file.

        Args:
            plist_path: Path to the Info.plist file.

        Returns:
            Dictionary with Info.plist data or None if parsing fails.
        """
        try:
            with open(plist_path, "rb") as f:
                plist = plistlib.load(f)

            # Extract basic info
            bundle_id = plist.get("CFBundleIdentifier", "")
            bundle_name = plist.get("CFBundleName", "") or plist.get("CFBundleDisplayName", "")
            version = plist.get("CFBundleShortVersionString", "")
            build = plist.get("CFBundleVersion", "")

            # Extract minimum iOS version
            min_ios_version = (
                plist.get("MinimumOSVersion", "")
                or plist.get("LSMinimumSystemVersion", "")
            )

            # Extract capabilities (from entitlements if present)
            capabilities = self._extract_capabilities(plist)

            # Extract privacy descriptions
            privacy_descriptions = self._extract_privacy_descriptions(plist)

            # Extract URL schemes
            url_schemes = self._extract_url_schemes(plist)

            return {
                "path": str(plist_path.relative_to(self.project_root)),
                "bundle_id": bundle_id,
                "bundle_name": bundle_name,
                "version": version,
                "build": build,
                "min_ios_version": min_ios_version,
                "capabilities": capabilities,
                "privacy_descriptions": privacy_descriptions,
                "url_schemes": url_schemes,
            }

        except plistlib.InvalidFileException as e:
            logger.warning(f"Invalid plist format in {plist_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error reading Info.plist {plist_path}: {e}")
            return None

    def _extract_capabilities(self, plist: dict[str, Any]) -> list[str]:
        """Extract capabilities from Info.plist.

        Args:
            plist: Parsed plist dictionary.

        Returns:
            List of detected capability keys.
        """
        capabilities: list[str] = []

        # Check for common capability indicators in Info.plist
        capability_indicators = {
            "UIBackgroundModes": "background-modes",
            "NSAppTransportSecurity": "app-transport-security",
            "UIRequiredDeviceCapabilities": "required-device-capabilities",
            "NSPrincipalClass": "principal-class",
            "UIApplicationSceneManifest": "scene-manifest",
            "ITSAppUsesNonExemptEncryption": "encryption-export-compliance",
        }

        for key, capability in capability_indicators.items():
            if key in plist:
                capabilities.append(capability)

        # Extract UIBackgroundModes values
        background_modes = plist.get("UIBackgroundModes", [])
        if isinstance(background_modes, list):
            for mode in background_modes:
                capabilities.append(f"background-{mode}")

        return capabilities

    def _extract_privacy_descriptions(self, plist: dict[str, Any]) -> dict[str, str]:
        """Extract privacy usage descriptions from Info.plist.

        Args:
            plist: Parsed plist dictionary.

        Returns:
            Dictionary mapping short privacy key names to descriptions.
        """
        privacy_descriptions: dict[str, str] = {}

        key_name_mapping = {
            "NSCameraUsageDescription": "camera",
            "NSPhotoLibraryUsageDescription": "photo_library",
            "NSPhotoLibraryAddUsageDescription": "photo_library_add",
            "NSMicrophoneUsageDescription": "microphone",
            "NSLocationWhenInUseUsageDescription": "location_when_in_use",
            "NSLocationAlwaysUsageDescription": "location_always",
            "NSLocationAlwaysAndWhenInUseUsageDescription": "location_always_and_when_in_use",
            "NSContactsUsageDescription": "contacts",
            "NSCalendarsUsageDescription": "calendars",
            "NSRemindersUsageDescription": "reminders",
            "NSHealthShareUsageDescription": "health_share",
            "NSHealthUpdateUsageDescription": "health_update",
            "NSMotionUsageDescription": "motion",
            "NSFaceIDUsageDescription": "face_id",
            "NSSpeechRecognitionUsageDescription": "speech_recognition",
            "NSAppleMusicUsageDescription": "apple_music",
            "NSBluetoothAlwaysUsageDescription": "bluetooth_always",
            "NSBluetoothPeripheralUsageDescription": "bluetooth_peripheral",
            "NSHomeKitUsageDescription": "homekit",
            "NSSiriUsageDescription": "siri",
            "NSUserTrackingUsageDescription": "user_tracking",
            "NSLocalNetworkUsageDescription": "local_network",
            "NSNearbyInteractionUsageDescription": "nearby_interaction",
        }

        for plist_key, short_name in key_name_mapping.items():
            if plist_key in plist:
                description = plist[plist_key]
                if isinstance(description, str):
                    privacy_descriptions[short_name] = description

        return privacy_descriptions

    def _extract_url_schemes(self, plist: dict[str, Any]) -> list[str]:
        """Extract URL schemes from Info.plist.

        Args:
            plist: Parsed plist dictionary.

        Returns:
            List of URL schemes.
        """
        url_schemes: list[str] = []

        url_types = plist.get("CFBundleURLTypes", [])
        if isinstance(url_types, list):
            for url_type in url_types:
                if isinstance(url_type, dict):
                    schemes = url_type.get("CFBundleURLSchemes", [])
                    if isinstance(schemes, list):
                        url_schemes.extend(schemes)

        return url_schemes

    def _analyze_swift_files(self) -> dict[str, Any]:
        """Analyze Swift files in the project.

        Returns:
            Dictionary containing:
            - count: Number of Swift files
            - directories: List of directories containing Swift files
            - interop_patterns: List of detected interop patterns
        """
        swift_info: dict[str, Any] = {
            "count": 0,
            "directories": [],
            "interop_patterns": [],
        }

        # Find all Swift files
        swift_files = list(self.project_root.rglob("*.swift"))
        swift_info["count"] = len(swift_files)

        # Collect unique directories
        directories: set[str] = set()
        for swift_file in swift_files:
            rel_path = swift_file.relative_to(self.project_root)
            # Get the top-level directory
            if len(rel_path.parts) > 1:
                directories.add(rel_path.parts[0])

        swift_info["directories"] = sorted(directories)

        # Detect interop patterns
        detected_patterns: set[str] = set()
        for swift_file in swift_files:
            try:
                content = swift_file.read_text(encoding="utf-8")
                for pattern_name, pattern in self.INTEROP_PATTERNS.items():
                    if pattern.search(content):
                        detected_patterns.add(pattern_name)
            except Exception as e:
                logger.warning(f"Error reading Swift file {swift_file}: {e}")

        # Also check Kotlin files for expect/actual patterns
        kotlin_files = list(self.project_root.rglob("*.kt"))
        for kotlin_file in kotlin_files:
            try:
                content = kotlin_file.read_text(encoding="utf-8")
                if self.INTEROP_PATTERNS["expect/actual"].search(content):
                    detected_patterns.add("expect/actual")
                if self.INTEROP_PATTERNS["@ObjCName"].search(content):
                    detected_patterns.add("@ObjCName")
                if self.INTEROP_PATTERNS["@HiddenFromObjC"].search(content):
                    detected_patterns.add("@HiddenFromObjC")
            except Exception as e:
                logger.warning(f"Error reading Kotlin file {kotlin_file}: {e}")

        swift_info["interop_patterns"] = sorted(detected_patterns)

        return swift_info

    def _analyze_dependencies(self) -> dict[str, Any]:
        """Analyze iOS dependency managers.

        Returns:
            Dictionary containing:
            - cocoapods: {has_podfile, pods}
            - spm: {has_package_swift, packages}
        """
        dependencies: dict[str, Any] = {
            "cocoapods": {"has_podfile": False, "pods": []},
            "spm": {"has_package_swift": False, "packages": []},
        }

        # Check for CocoaPods
        podfile = self.project_root / "Podfile"
        if not podfile.exists():
            # Check in iosApp subdirectory
            podfile = self.project_root / "iosApp" / "Podfile"

        if podfile.exists():
            dependencies["cocoapods"]["has_podfile"] = True
            dependencies["cocoapods"]["pods"] = self._parse_podfile(podfile)

        # Check for Swift Package Manager
        package_swift = self.project_root / "Package.swift"
        if not package_swift.exists():
            # Check in iosApp subdirectory
            package_swift = self.project_root / "iosApp" / "Package.swift"

        if package_swift.exists():
            dependencies["spm"]["has_package_swift"] = True
            dependencies["spm"]["packages"] = self._parse_package_swift(package_swift)

        return dependencies

    def _parse_podfile(self, podfile_path: Path) -> list[str]:
        """Parse Podfile to extract pod dependencies.

        Args:
            podfile_path: Path to Podfile.

        Returns:
            List of pod names.
        """
        pods: list[str] = []

        try:
            content = podfile_path.read_text(encoding="utf-8")

            # Match pod declarations: pod 'PodName' or pod "PodName"
            pod_pattern = re.compile(r"^\s*pod\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
            for match in pod_pattern.finditer(content):
                pod_name = match.group(1)
                # Extract just the pod name (before any version specifier)
                pod_name = pod_name.split(",")[0].strip()
                if pod_name and pod_name not in pods:
                    pods.append(pod_name)

        except Exception as e:
            logger.warning(f"Error parsing Podfile {podfile_path}: {e}")

        return pods

    def _parse_package_swift(self, package_path: Path) -> list[str]:
        """Parse Package.swift to extract SPM dependencies.

        Args:
            package_path: Path to Package.swift.

        Returns:
            List of package names.
        """
        packages: list[str] = []

        try:
            content = package_path.read_text(encoding="utf-8")

            # Match .package(url: "...") or .package(name: "...")
            # Extract package name from URL or name parameter
            url_pattern = re.compile(
                r'\.package\s*\(\s*(?:name:\s*"([^"]+)".*?)?url:\s*"([^"]+)"',
                re.MULTILINE | re.DOTALL
            )
            for match in url_pattern.finditer(content):
                name = match.group(1)
                url = match.group(2)

                if name:
                    packages.append(name)
                elif url:
                    # Extract package name from URL
                    # e.g., https://github.com/Alamofire/Alamofire.git -> Alamofire
                    package_name = url.rstrip("/").rstrip(".git").split("/")[-1]
                    if package_name and package_name not in packages:
                        packages.append(package_name)

            # Also match .package(name: "...", path: "...")
            path_pattern = re.compile(
                r'\.package\s*\(\s*name:\s*"([^"]+)"',
                re.MULTILINE
            )
            for match in path_pattern.finditer(content):
                name = match.group(1)
                if name and name not in packages:
                    packages.append(name)

        except Exception as e:
            logger.warning(f"Error parsing Package.swift {package_path}: {e}")

        return packages

    def _detect_xcode_project(self) -> dict[str, Any]:
        """Detect Xcode project or workspace.

        Returns:
            Dictionary containing:
            - name: Project name
            - path: Relative path to .xcodeproj or .xcworkspace
        """
        xcode_project: dict[str, Any] = {}

        # First check for .xcworkspace (preferred over .xcodeproj)
        workspaces = list(self.project_root.rglob("*.xcworkspace"))
        # Filter out internal xcworkspace inside xcodeproj
        workspaces = [
            ws for ws in workspaces
            if not any(part.endswith(".xcodeproj") for part in ws.parts)
        ]

        if workspaces:
            workspace = workspaces[0]
            xcode_project["name"] = workspace.stem
            xcode_project["path"] = str(workspace.relative_to(self.project_root))
            xcode_project["type"] = "workspace"
            return xcode_project

        # Check for .xcodeproj
        projects = list(self.project_root.rglob("*.xcodeproj"))
        if projects:
            project = projects[0]
            xcode_project["name"] = project.stem
            xcode_project["path"] = str(project.relative_to(self.project_root))
            xcode_project["type"] = "project"
            return xcode_project

        return xcode_project

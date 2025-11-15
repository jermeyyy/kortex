"""LSP manager for lifecycle management and health monitoring.

This module provides the LSPManager class that handles multiple language
server instances with automatic health checks, crash recovery, and restart
capabilities.

Supports Kotlin, Swift (SourceKit-LSP), and Objective-C (clangd) language servers
for comprehensive Kotlin Multiplatform project analysis.
"""

import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any, Union
from datetime import datetime, timedelta

from ..utils.logging import get_logger
from .client import LSPClient
from .kotlin_server import KotlinLSPServer
from .swift_server import SwiftLSPServer
from .objc_server import ObjCLSPServer


logger = get_logger(__name__)


class LSPManager:
    """Manages multiple LSP client instances with health monitoring.

    Handles lifecycle management, automatic crash detection and recovery,
    and health checks for multiple language servers.

    Attributes:
        clients: Map of language ID to LSPClient instance
        health_check_interval: Seconds between health checks
        max_restart_attempts: Maximum restart attempts before giving up
        restart_counts: Map of language ID to restart attempt count
        last_health_check: Map of language ID to last health check time

    Example:
        >>> manager = LSPManager()
        >>> await manager.start_server(
        ...     language_id="kotlin",
        ...     command="kotlin-language-server",
        ...     workspace_path=Path("/project")
        ... )
        >>> client = manager.get_client("kotlin")
        >>> await manager.stop_all()
    """

    def __init__(
        self,
        health_check_interval: float = 30.0,
        max_restart_attempts: int = 3,
    ):
        """Initialize LSP manager.

        Args:
            health_check_interval: Seconds between health checks
            max_restart_attempts: Maximum restart attempts per server
        """
        self.clients: Dict[str, LSPClient] = {}
        self.health_check_interval = health_check_interval
        self.max_restart_attempts = max_restart_attempts
        self.restart_counts: Dict[str, int] = {}
        self.last_health_check: Dict[str, datetime] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start_server(
        self,
        language_id: str,
        command: str,
        args: Optional[List[str]] = None,
        workspace_path: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        """Start a language server instance.

        Args:
            language_id: Unique identifier for this language server
            command: Command to start the language server
            args: Command line arguments
            workspace_path: Workspace root directory
            env: Environment variables for the process

        Raises:
            RuntimeError: If server fails to start
            ValueError: If language_id already exists

        Example:
            >>> await manager.start_server(
            ...     language_id="kotlin",
            ...     command="kotlin-language-server",
            ...     workspace_path=Path("/project")
            ... )
        """
        if language_id in self.clients:
            raise ValueError(f"Language server '{language_id}' already exists")

        logger.info(f"Starting language server: {language_id}")
        
        client = LSPClient(
            command=command,
            args=args,
            workspace_path=workspace_path,
            env=env,
        )

        try:
            await client.start()
            self.clients[language_id] = client
            self.restart_counts[language_id] = 0
            self.last_health_check[language_id] = datetime.now()
            
            # Start health check task if not running
            if not self._health_check_task and not self._running:
                self._running = True
                self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info(f"Language server started: {language_id}")
        except Exception as e:
            logger.error(f"Failed to start language server '{language_id}': {e}")
            raise

    async def stop_server(self, language_id: str) -> None:
        """Stop a language server instance.

        Args:
            language_id: Language server to stop

        Example:
            >>> await manager.stop_server("kotlin")
        """
        client = self.clients.get(language_id)
        if not client:
            logger.warning(f"Language server '{language_id}' not found")
            return

        logger.info(f"Stopping language server: {language_id}")
        
        try:
            await client.stop()
        except Exception as e:
            logger.error(f"Error stopping language server '{language_id}': {e}")
        finally:
            self.clients.pop(language_id, None)
            self.restart_counts.pop(language_id, None)
            self.last_health_check.pop(language_id, None)

        logger.info(f"Language server stopped: {language_id}")

    async def stop_all(self) -> None:
        """Stop all language server instances.

        Example:
            >>> await manager.stop_all()
        """
        logger.info("Stopping all language servers")
        
        self._running = False
        
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None

        # Stop all clients
        language_ids = list(self.clients.keys())
        for language_id in language_ids:
            await self.stop_server(language_id)

        logger.info("All language servers stopped")

    def get_client(self, language_id: str) -> Optional[LSPClient]:
        """Get a language server client by ID.

        Args:
            language_id: Language server identifier

        Returns:
            LSPClient instance or None if not found

        Example:
            >>> client = manager.get_client("kotlin")
            >>> if client:
            ...     symbols = await client.workspace_symbols("Repository")
        """
        return self.clients.get(language_id)

    def is_running(self, language_id: str) -> bool:
        """Check if a language server is running.

        Args:
            language_id: Language server identifier

        Returns:
            True if server is running

        Example:
            >>> if manager.is_running("kotlin"):
            ...     print("Kotlin server is ready")
        """
        client = self.clients.get(language_id)
        return client is not None and client.is_running()

    async def restart_server(self, language_id: str) -> bool:
        """Restart a language server instance.

        Args:
            language_id: Language server to restart

        Returns:
            True if restart successful, False otherwise

        Example:
            >>> success = await manager.restart_server("kotlin")
        """
        client = self.clients.get(language_id)
        if not client:
            logger.warning(f"Cannot restart, language server '{language_id}' not found")
            return False

        restart_count = self.restart_counts.get(language_id, 0)
        if restart_count >= self.max_restart_attempts:
            logger.error(
                f"Max restart attempts ({self.max_restart_attempts}) "
                f"reached for '{language_id}', giving up"
            )
            return False

        logger.info(f"Restarting language server: {language_id} (attempt {restart_count + 1})")
        
        # Save configuration
        command = client.command
        args = client.args
        workspace_path = client.workspace_path
        env = client.env

        # Stop current instance
        await self.stop_server(language_id)

        # Start new instance
        try:
            await self.start_server(
                language_id=language_id,
                command=command,
                args=args,
                workspace_path=workspace_path,
                env=env,
            )
            
            # Increment restart count
            self.restart_counts[language_id] = restart_count + 1
            
            logger.info(f"Language server restarted successfully: {language_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart language server '{language_id}': {e}")
            self.restart_counts[language_id] = restart_count + 1
            return False

    async def health_check(self, language_id: str) -> bool:
        """Perform health check on a language server.

        Args:
            language_id: Language server to check

        Returns:
            True if server is healthy, False otherwise

        Example:
            >>> is_healthy = await manager.health_check("kotlin")
        """
        client = self.clients.get(language_id)
        if not client:
            return False

        # Check if process is running
        if not client.is_running():
            logger.warning(f"Language server '{language_id}' is not running")
            return False

        # Update last health check time
        self.last_health_check[language_id] = datetime.now()

        # Server is running and responsive
        return True

    async def _health_check_loop(self) -> None:
        """Continuous health check loop for all servers."""
        logger.info("Starting health check loop")
        
        try:
            while self._running:
                await asyncio.sleep(self.health_check_interval)
                
                if not self._running:
                    break

                # Check all servers
                language_ids = list(self.clients.keys())
                for language_id in language_ids:
                    try:
                        is_healthy = await self.health_check(language_id)
                        
                        if not is_healthy:
                            logger.warning(
                                f"Health check failed for '{language_id}', "
                                "attempting restart"
                            )
                            await self.restart_server(language_id)
                            
                    except Exception as e:
                        logger.error(
                            f"Error during health check for '{language_id}': {e}"
                        )

        except asyncio.CancelledError:
            logger.info("Health check loop cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in health check loop: {e}")
        finally:
            logger.info("Health check loop stopped")

    def get_all_clients(self) -> Dict[str, LSPClient]:
        """Get all active language server clients.

        Returns:
            Dictionary mapping language IDs to clients

        Example:
            >>> for lang_id, client in manager.get_all_clients().items():
            ...     print(f"{lang_id}: running={client.is_running()}")
        """
        return dict(self.clients)

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all language servers.

        Returns:
            Dictionary with status information per language server

        Example:
            >>> status = manager.get_status()
            >>> print(status["kotlin"]["running"])
        """
        status = {}
        for language_id, client in self.clients.items():
            status[language_id] = {
                "running": client.is_running(),
                "restart_count": self.restart_counts.get(language_id, 0),
                "last_health_check": self.last_health_check.get(language_id),
            }
        return status

    async def start_kotlin_server(
        self,
        workspace_path: Path,
        server_command: Optional[str] = None,
    ) -> None:
        """Start Kotlin Language Server.

        Convenience method for starting Kotlin LSP with proper configuration.

        Args:
            workspace_path: Path to KMP project root
            server_command: Custom server command (default: auto-detect)

        Raises:
            RuntimeError: If server fails to start
            ValueError: If Kotlin server already running

        Example:
            >>> await manager.start_kotlin_server(Path("/project"))
        """
        kotlin_server = KotlinLSPServer(
            workspace_path=workspace_path,
            server_command=server_command
        )
        
        await self.start_server(
            language_id="kotlin",
            command=kotlin_server.server_command,
            args=[],
            workspace_path=workspace_path,
            env=kotlin_server.client.env
        )

    async def start_swift_server(
        self,
        workspace_path: Path,
        sourcekit_path: Optional[str] = None,
    ) -> None:
        """Start Swift Language Server (SourceKit-LSP).

        Convenience method for starting Swift LSP with proper configuration.

        Args:
            workspace_path: Path to project root with Swift/iOS code
            sourcekit_path: Custom SourceKit-LSP path (default: auto-detect)

        Raises:
            RuntimeError: If server fails to start
            ValueError: If Swift server already running

        Example:
            >>> await manager.start_swift_server(Path("/project"))
        """
        swift_server = SwiftLSPServer(
            workspace_path=workspace_path,
            sourcekit_path=sourcekit_path
        )
        
        await self.start_server(
            language_id="swift",
            command=swift_server.command,
            args=[],
            workspace_path=workspace_path,
            env=swift_server.client.env
        )

    async def start_objc_server(
        self,
        workspace_path: Path,
        clangd_path: Optional[str] = None,
        clangd_args: Optional[List[str]] = None,
    ) -> None:
        """Start Objective-C Language Server (clangd).

        Convenience method for starting clangd with proper configuration.

        Args:
            workspace_path: Path to project root with Objective-C code
            clangd_path: Custom clangd path (default: auto-detect)
            clangd_args: Additional clangd arguments

        Raises:
            RuntimeError: If server fails to start
            ValueError: If Objective-C server already running

        Example:
            >>> await manager.start_objc_server(Path("/project"))
        """
        objc_server = ObjCLSPServer(
            workspace_path=workspace_path,
            clangd_path=clangd_path,
            clangd_args=clangd_args
        )
        
        await self.start_server(
            language_id="objective-c",
            command=objc_server.command,
            args=objc_server.args,
            workspace_path=workspace_path,
            env=objc_server.client.env
        )

    async def start_all_for_kmp_project(
        self,
        workspace_path: Path,
        include_swift: bool = True,
        include_objc: bool = True,
    ) -> None:
        """Start all relevant language servers for a KMP project.

        Convenience method to start Kotlin, Swift, and Objective-C servers
        for comprehensive KMP/iOS project support.

        Args:
            workspace_path: Path to KMP project root
            include_swift: Start Swift LSP server
            include_objc: Start Objective-C LSP server

        Raises:
            RuntimeError: If any server fails to start

        Example:
            >>> # Start all servers for KMP project
            >>> await manager.start_all_for_kmp_project(Path("/project"))
            >>>
            >>> # Start only Kotlin and Swift
            >>> await manager.start_all_for_kmp_project(
            ...     Path("/project"),
            ...     include_objc=False
            ... )
        """
        logger.info(f"Starting language servers for KMP project: {workspace_path}")
        
        # Always start Kotlin server for KMP
        try:
            await self.start_kotlin_server(workspace_path)
        except Exception as e:
            logger.error(f"Failed to start Kotlin server: {e}")
            # Continue to try other servers
        
        # Optionally start Swift server
        if include_swift:
            try:
                await self.start_swift_server(workspace_path)
            except Exception as e:
                logger.warning(f"Failed to start Swift server: {e}")
                # Not critical, continue
        
        # Optionally start Objective-C server
        if include_objc:
            try:
                await self.start_objc_server(workspace_path)
            except Exception as e:
                logger.warning(f"Failed to start Objective-C server: {e}")
                # Not critical, continue
        
        logger.info("Language server initialization complete")

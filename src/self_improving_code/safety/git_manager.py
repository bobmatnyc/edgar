"""
Git-based Safety Manager

Provides git-based safety mechanisms for the self-improving code pattern.
"""

import os
import subprocess
from datetime import datetime
from typing import Optional

import structlog

from ..core.interfaces import SafetyManager

logger = structlog.get_logger(__name__)


class GitSafetyManager(SafetyManager):
    """
    Git-based safety manager for self-improving code.

    Creates git branches and commits as checkpoints, enabling
    safe rollback if code improvements fail.
    """

    def __init__(self, base_branch: str = "main"):
        """
        Initialize Git safety manager.

        Args:
            base_branch: Base branch to return to on rollback
        """
        self.base_branch = base_branch
        self._ensure_git_repo()

        logger.info("Git Safety Manager initialized", base_branch=base_branch)

    def _ensure_git_repo(self):
        """Ensure we're in a git repository."""
        try:
            result = subprocess.run(
                ["git", "status"], check=True, capture_output=True, text=True
            )
            logger.debug("Git repository confirmed")
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "Must be in a git repository for safety. "
                "Initialize with 'git init' if needed."
            )

    def create_checkpoint(self, message: str) -> str:
        """
        Create a git checkpoint before making changes.

        Args:
            message: Commit message describing the checkpoint

        Returns:
            Checkpoint ID (branch name) for rollback
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"self_improve_{timestamp}"

        try:
            # Stash any uncommitted changes
            subprocess.run(
                ["git", "stash", "push", "-m", f"Pre-checkpoint stash: {message}"],
                capture_output=True,
                text=True,
            )

            # Create and switch to new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True,
                capture_output=True,
                text=True,
            )

            # Add all changes
            subprocess.run(
                ["git", "add", "."], check=True, capture_output=True, text=True
            )

            # Commit current state
            subprocess.run(
                ["git", "commit", "-m", f"Checkpoint: {message}"],
                check=True,
                capture_output=True,
                text=True,
            )

            logger.info("Git checkpoint created", branch=branch_name, message=message)

            return branch_name

        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to create git checkpoint",
                error=str(e),
                stderr=e.stderr if hasattr(e, "stderr") else None,
            )
            raise RuntimeError(f"Git checkpoint creation failed: {e}")

    def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Rollback to a previous checkpoint.

        Args:
            checkpoint_id: Checkpoint ID (branch name) to rollback to

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Switch back to base branch
            subprocess.run(
                ["git", "checkout", self.base_branch],
                check=True,
                capture_output=True,
                text=True,
            )

            # Delete the checkpoint branch
            subprocess.run(
                ["git", "branch", "-D", checkpoint_id],
                check=True,
                capture_output=True,
                text=True,
            )

            # Restore any stashed changes
            stash_result = subprocess.run(
                ["git", "stash", "list"], capture_output=True, text=True
            )

            if stash_result.stdout and "Pre-checkpoint stash" in stash_result.stdout:
                subprocess.run(["git", "stash", "pop"], capture_output=True, text=True)

            logger.info(
                "Rolled back to checkpoint",
                deleted_branch=checkpoint_id,
                current_branch=self.base_branch,
            )

            return True

        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to rollback to checkpoint",
                checkpoint=checkpoint_id,
                error=str(e),
                stderr=e.stderr if hasattr(e, "stderr") else None,
            )
            return False

    def list_checkpoints(self) -> list:
        """List all available checkpoints."""
        try:
            result = subprocess.run(
                ["git", "branch"], capture_output=True, text=True, check=True
            )

            branches = []
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("self_improve_"):
                    branches.append(line.replace("* ", ""))

            return branches

        except subprocess.CalledProcessError:
            return []

    def cleanup_old_checkpoints(self, keep_latest: int = 5) -> int:
        """
        Clean up old checkpoint branches.

        Args:
            keep_latest: Number of latest checkpoints to keep

        Returns:
            Number of checkpoints cleaned up
        """
        checkpoints = self.list_checkpoints()

        if len(checkpoints) <= keep_latest:
            return 0

        # Sort by timestamp (embedded in branch name)
        checkpoints.sort()
        to_delete = checkpoints[:-keep_latest]

        deleted_count = 0
        for checkpoint in to_delete:
            try:
                subprocess.run(
                    ["git", "branch", "-D", checkpoint],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                deleted_count += 1
                logger.debug("Cleaned up old checkpoint", branch=checkpoint)
            except subprocess.CalledProcessError as e:
                logger.warning(
                    "Failed to delete checkpoint", branch=checkpoint, error=str(e)
                )

        if deleted_count > 0:
            logger.info(
                "Cleaned up old checkpoints",
                deleted=deleted_count,
                kept=len(checkpoints) - deleted_count,
            )

        return deleted_count

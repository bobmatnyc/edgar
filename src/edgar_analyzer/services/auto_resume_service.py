"""Auto-resume service for intelligent checkpoint detection and resumption."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import structlog

from edgar_analyzer.models.intermediate_data import AnalysisCheckpoint, CheckpointManager

logger = structlog.get_logger(__name__)


class AutoResumeService:
    """Service for intelligent auto-resume functionality."""

    def __init__(self, checkpoint_manager: CheckpointManager):
        """Initialize auto-resume service."""
        self._checkpoint_manager = checkpoint_manager
        logger.info("Auto-resume service initialized")

    def analyze_resume_options(
        self,
        target_year: int,
        company_count: int,
        max_age_hours: int = 24
    ) -> Dict[str, any]:
        """Analyze available resume options and provide recommendations."""

        checkpoints = self._checkpoint_manager.list_checkpoints()

        # Filter relevant checkpoints
        relevant_checkpoints = []
        for cp in checkpoints:
            if cp.get("target_year") == target_year:
                try:
                    last_updated = datetime.fromisoformat(cp["last_updated"])
                    age_hours = (datetime.now() - last_updated).total_seconds() / 3600

                    if age_hours <= max_age_hours:
                        cp["age_hours"] = age_hours
                        cp["company_count_diff"] = abs(cp.get("total_companies", 0) - company_count)
                        relevant_checkpoints.append(cp)
                except (ValueError, KeyError):
                    continue

        if not relevant_checkpoints:
            return {
                "recommendation": "start_new",
                "reason": "No recent checkpoints found",
                "options": []
            }

        # Categorize checkpoints
        incomplete = [cp for cp in relevant_checkpoints if cp.get("progress", 100) < 100]
        complete = [cp for cp in relevant_checkpoints if cp.get("progress", 100) >= 100]

        # Find best resume candidate
        best_candidate = None
        recommendation = "start_new"
        reason = "No suitable checkpoint found"

        if incomplete:
            # Sort incomplete by progress (descending) and company count similarity
            incomplete.sort(key=lambda cp: (-cp.get("progress", 0), cp["company_count_diff"]))

            candidate = incomplete[0]
            progress = candidate.get("progress", 0)
            company_diff = candidate["company_count_diff"]

            if progress > 10 and company_diff <= company_count * 0.2:  # 20% tolerance
                best_candidate = candidate
                recommendation = "auto_resume"
                reason = f"Found incomplete analysis with {progress:.1f}% progress"
            elif progress > 50:  # High progress, even if company count differs
                best_candidate = candidate
                recommendation = "suggest_resume"
                reason = f"Found high-progress analysis ({progress:.1f}%) but different company count"

        elif complete:
            # Check if we want to suggest re-running a recent complete analysis
            recent_complete = [cp for cp in complete if cp["age_hours"] < 6]  # Last 6 hours

            if recent_complete:
                candidate = recent_complete[0]
                if candidate["company_count_diff"] <= company_count * 0.1:  # 10% tolerance
                    best_candidate = candidate
                    recommendation = "suggest_rerun"
                    reason = "Found recent complete analysis with similar parameters"

        return {
            "recommendation": recommendation,
            "reason": reason,
            "best_candidate": best_candidate,
            "incomplete_count": len(incomplete),
            "complete_count": len(complete),
            "total_relevant": len(relevant_checkpoints),
            "options": relevant_checkpoints[:5]  # Top 5 options
        }

    def get_auto_resume_decision(
        self,
        target_year: int,
        company_count: int,
        auto_resume_enabled: bool = True,
        force_new: bool = False
    ) -> Tuple[str, Optional[AnalysisCheckpoint], Dict[str, any]]:
        """Get auto-resume decision with detailed reasoning."""

        if force_new:
            return "start_new", None, {"reason": "Force new analysis requested"}

        if not auto_resume_enabled:
            return "start_new", None, {"reason": "Auto-resume disabled"}

        # Analyze options
        analysis = self.analyze_resume_options(target_year, company_count)

        recommendation = analysis["recommendation"]
        best_candidate = analysis["best_candidate"]

        if recommendation == "auto_resume" and best_candidate:
            # Load the full checkpoint
            checkpoint = self._checkpoint_manager.load_checkpoint(
                best_candidate["analysis_id"],
                best_candidate["target_year"]
            )

            if checkpoint:
                logger.info(
                    "Auto-resume decision: resume",
                    analysis_id=checkpoint.analysis_id,
                    progress=f"{checkpoint.progress_percentage:.1f}%",
                    reason=analysis["reason"]
                )
                return "auto_resume", checkpoint, analysis

        elif recommendation in ["suggest_resume", "suggest_rerun"]:
            # Load checkpoint for suggestion
            checkpoint = self._checkpoint_manager.load_checkpoint(
                best_candidate["analysis_id"],
                best_candidate["target_year"]
            ) if best_candidate else None

            logger.info(
                "Auto-resume decision: suggest",
                suggestion=recommendation,
                reason=analysis["reason"]
            )
            return "suggest", checkpoint, analysis

        # Default to starting new
        logger.info("Auto-resume decision: start new", reason=analysis["reason"])
        return "start_new", None, analysis

    def format_resume_suggestion(self, analysis: Dict[str, any]) -> str:
        """Format a human-readable resume suggestion."""

        recommendation = analysis["recommendation"]
        best_candidate = analysis["best_candidate"]

        if recommendation == "auto_resume":
            return (
                f"🔄 Auto-resuming analysis '{best_candidate['analysis_id']}' "
                f"({best_candidate['progress']:.1f}% complete, "
                f"{best_candidate['completed_companies']}/{best_candidate['total_companies']} companies)"
            )

        elif recommendation == "suggest_resume":
            return (
                f"💡 Found incomplete analysis '{best_candidate['analysis_id']}' "
                f"({best_candidate['progress']:.1f}% complete). "
                f"Resume with: --resume {best_candidate['analysis_id']}"
            )

        elif recommendation == "suggest_rerun":
            return (
                f"💡 Found recent complete analysis '{best_candidate['analysis_id']}'. "
                f"Resume/rerun with: --resume {best_candidate['analysis_id']}"
            )

        else:
            return "🆕 Starting new analysis (no suitable checkpoints found)"
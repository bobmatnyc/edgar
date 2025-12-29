"""Intermediate data structures for checkpoint/resume functionality."""

import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ExtractionStatus(str, Enum):
    """Status of data extraction for a company."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CompanyExtractionData(BaseModel):
    """Intermediate data structure for a single company's extracted data."""

    # Company identification
    cik: str = Field(..., description="SEC CIK identifier")
    name: str = Field(..., description="Company name")
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    fortune_rank: Optional[int] = Field(None, description="Fortune 500 ranking")
    sector: Optional[str] = Field(None, description="Business sector")
    industry: Optional[str] = Field(None, description="Industry classification")

    # Extraction metadata
    status: ExtractionStatus = Field(default=ExtractionStatus.PENDING, description="Extraction status")
    extraction_start_time: Optional[datetime] = Field(None, description="When extraction started")
    extraction_end_time: Optional[datetime] = Field(None, description="When extraction completed")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")

    # Financial data by year
    tax_data: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Tax expense data by year")
    compensation_data: Dict[int, List[Dict[str, Any]]] = Field(default_factory=dict, description="Executive compensation by year")

    # Calculated metrics
    total_compensation_by_year: Dict[int, Decimal] = Field(default_factory=dict, description="Total compensation by year")
    compensation_vs_tax_ratios: Dict[int, Optional[float]] = Field(default_factory=dict, description="Compensation to tax ratios")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class AnalysisCheckpoint(BaseModel):
    """Checkpoint data for resuming interrupted analyses."""

    # Analysis metadata
    analysis_id: str = Field(..., description="Unique analysis identifier")
    target_year: int = Field(..., description="Primary analysis year")
    analysis_years: List[int] = Field(..., description="All years being analyzed")
    total_companies: int = Field(..., description="Total number of companies to analyze")

    # Progress tracking
    created_at: datetime = Field(default_factory=datetime.now, description="Checkpoint creation time")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update time")
    completed_companies: int = Field(default=0, description="Number of completed companies")
    failed_companies: int = Field(default=0, description="Number of failed companies")

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Analysis configuration")

    # Company data
    companies: List[CompanyExtractionData] = Field(default_factory=list, description="Company extraction data")

    # Error tracking
    global_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Global errors encountered")

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_companies == 0:
            return 0.0
        return (self.completed_companies + self.failed_companies) / self.total_companies * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total_processed = self.completed_companies + self.failed_companies
        if total_processed == 0:
            return 0.0
        return self.completed_companies / total_processed * 100

    def get_company_by_cik(self, cik: str) -> Optional[CompanyExtractionData]:
        """Get company data by CIK."""
        for company in self.companies:
            if company.cik == cik:
                return company
        return None

    def get_pending_companies(self) -> List[CompanyExtractionData]:
        """Get list of companies that still need processing."""
        return [c for c in self.companies if c.status == ExtractionStatus.PENDING]

    def get_failed_companies(self) -> List[CompanyExtractionData]:
        """Get list of companies that failed extraction."""
        return [c for c in self.companies if c.status == ExtractionStatus.FAILED]

    def get_completed_companies(self) -> List[CompanyExtractionData]:
        """Get list of successfully completed companies."""
        return [c for c in self.companies if c.status == ExtractionStatus.COMPLETED]

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class CheckpointManager:
    """Manager for saving and loading analysis checkpoints."""

    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        """Initialize checkpoint manager."""
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, checkpoint: AnalysisCheckpoint) -> Path:
        """Save checkpoint to disk."""
        checkpoint.last_updated = datetime.now()

        filename = f"analysis_{checkpoint.analysis_id}_{checkpoint.target_year}.json"
        filepath = self.checkpoint_dir / filename

        # Convert to dict and handle special types
        checkpoint_dict = checkpoint.dict()

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_dict, f, indent=2, default=self._json_serializer)

        return filepath

    def load_checkpoint(self, analysis_id: str, target_year: int) -> Optional[AnalysisCheckpoint]:
        """Load checkpoint from disk."""
        filename = f"analysis_{analysis_id}_{target_year}.json"
        filepath = self.checkpoint_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                checkpoint_dict = json.load(f)

            # Convert datetime strings back to datetime objects
            checkpoint_dict = self._deserialize_checkpoint(checkpoint_dict)

            return AnalysisCheckpoint(**checkpoint_dict)

        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return None

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints."""
        checkpoints = []

        for filepath in self.checkpoint_dir.glob("analysis_*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                checkpoints.append({
                    "analysis_id": data.get("analysis_id"),
                    "target_year": data.get("target_year"),
                    "created_at": data.get("created_at"),
                    "last_updated": data.get("last_updated"),
                    "total_companies": data.get("total_companies"),
                    "completed_companies": data.get("completed_companies"),
                    "progress": data.get("completed_companies", 0) / data.get("total_companies", 1) * 100,
                    "filepath": str(filepath)
                })
            except Exception:
                continue

        return sorted(checkpoints, key=lambda x: x.get("last_updated", ""), reverse=True)

    def find_resumable_analysis(
        self,
        target_year: int,
        company_count: Optional[int] = None,
        max_age_hours: int = 24
    ) -> Optional[AnalysisCheckpoint]:
        """Find the best resumable analysis for the given criteria."""
        checkpoints = self.list_checkpoints()

        # Filter by target year
        year_checkpoints = [cp for cp in checkpoints if cp.get("target_year") == target_year]

        if not year_checkpoints:
            return None

        # Filter by age (within last 24 hours by default)
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        recent_checkpoints = []
        for cp in year_checkpoints:
            try:
                last_updated = datetime.fromisoformat(cp["last_updated"])
                if last_updated > cutoff_time:
                    recent_checkpoints.append(cp)
            except (ValueError, KeyError):
                continue

        if not recent_checkpoints:
            return None

        # Find incomplete analyses (progress < 100%)
        incomplete_checkpoints = [
            cp for cp in recent_checkpoints
            if cp.get("progress", 100) < 100
        ]

        # If we have incomplete analyses, prioritize them
        if incomplete_checkpoints:
            candidates = incomplete_checkpoints
        else:
            # Otherwise, consider recent complete analyses for potential re-run
            candidates = recent_checkpoints

        # If company count is specified, prefer analyses with similar company count
        if company_count:
            # Sort by how close the company count is to our target
            candidates.sort(key=lambda cp: abs(cp.get("total_companies", 0) - company_count))

        # Get the best candidate
        best_candidate = candidates[0]

        # Load the full checkpoint
        return self.load_checkpoint(
            best_candidate["analysis_id"],
            best_candidate["target_year"]
        )

    def should_auto_resume(
        self,
        target_year: int,
        company_count: int,
        force_new: bool = False
    ) -> tuple[bool, Optional[AnalysisCheckpoint]]:
        """Determine if we should auto-resume an existing analysis."""

        if force_new:
            return False, None

        # Look for resumable analysis
        resumable = self.find_resumable_analysis(target_year, company_count)

        if not resumable:
            return False, None

        # Check if it's worth resuming
        progress = resumable.progress_percentage

        # Auto-resume if:
        # 1. Analysis is incomplete (< 100%)
        # 2. Analysis has made significant progress (> 10%) to avoid resuming barely started analyses
        # 3. Company count is similar (within 20% difference)

        company_count_diff = abs(resumable.total_companies - company_count) / company_count * 100

        should_resume = (
            progress < 100 and  # Incomplete
            progress > 10 and   # Has made some progress
            company_count_diff <= 20  # Similar company count
        )

        return should_resume, resumable

    def get_auto_resume_summary(self, checkpoint: AnalysisCheckpoint) -> Dict[str, Any]:
        """Get summary information for auto-resume decision."""
        return {
            "analysis_id": checkpoint.analysis_id,
            "target_year": checkpoint.target_year,
            "progress_percentage": checkpoint.progress_percentage,
            "completed_companies": checkpoint.completed_companies,
            "total_companies": checkpoint.total_companies,
            "failed_companies": checkpoint.failed_companies,
            "success_rate": checkpoint.success_rate,
            "last_updated": checkpoint.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
            "age_hours": (datetime.now() - checkpoint.last_updated).total_seconds() / 3600,
            "estimated_remaining": checkpoint.total_companies - checkpoint.completed_companies - checkpoint.failed_companies
        }

    def delete_checkpoint(self, analysis_id: str, target_year: int) -> bool:
        """Delete a checkpoint file."""
        filename = f"analysis_{analysis_id}_{target_year}.json"
        filepath = self.checkpoint_dir / filename

        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for special types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _deserialize_checkpoint(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize checkpoint data, converting strings back to proper types."""
        # Convert datetime strings
        for field in ["created_at", "last_updated"]:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field])
                except ValueError:
                    pass

        # Convert company data
        if "companies" in data:
            for company in data["companies"]:
                for field in ["extraction_start_time", "extraction_end_time"]:
                    if field in company and isinstance(company[field], str):
                        try:
                            company[field] = datetime.fromisoformat(company[field])
                        except ValueError:
                            pass

                # Convert Decimal fields
                if "total_compensation_by_year" in company:
                    company["total_compensation_by_year"] = {
                        int(k): Decimal(str(v)) for k, v in company["total_compensation_by_year"].items()
                    }

        return data
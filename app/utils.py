"""
Shared utility helpers used across multiple routers.
"""
from app.constants import PIPELINE_PROBABILITIES


def get_db_probabilities(db) -> dict:
    """Load pipeline stage probabilities from DB, fall back to constants.

    Returns a dict mapping stage name -> probability (0-100).
    """
    from app.models.models import AppStage
    stages = db.query(AppStage).filter(AppStage.stage_type == 'pipeline').all()
    if stages:
        return {s.name: (s.probability or 0) for s in stages}
    return dict(PIPELINE_PROBABILITIES)

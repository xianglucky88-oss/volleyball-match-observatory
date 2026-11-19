"""排球比赛观测数据"""

from . import touch_evidence, lineup_spells, receive_zones, setter_choices, annotation_agreement
from .contract import Row

PIPELINES = {
    "touch-evidence": touch_evidence.build_facts,
    "lineup-spells": lineup_spells.build_facts,
    "receive-zones": receive_zones.build_facts,
    "setter-choices": setter_choices.build_facts,
    "annotation-agreement": annotation_agreement.build_facts,
}

def process(pipeline: str, data: Row) -> list[Row]:
    """Validate and transform an independent input dataset into keyed facts."""
    if pipeline not in PIPELINES:
        raise ValueError(f"unknown pipeline: {pipeline}")
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    return PIPELINES[pipeline](data)

"""Predefined Cypher query templates package"""

from .base_templates import (
    QueryTemplate,
    BaseTemplateLibrary,
    ParameterExtractor,
)
from .drug_repurposing import (
    DrugRepurposingTemplates,
    get_drug_repurposing_templates,
)
from .target_identification import (
    TargetIdentificationTemplates,
    get_target_identification_templates,
)
from .indication_expansion import (
    IndicationExpansionTemplates,
    get_indication_expansion_templates,
)
from typing import List


def get_all_template_libraries() -> List[BaseTemplateLibrary]:
    """Get all template libraries"""
    return [
        get_drug_repurposing_templates(),
        get_target_identification_templates(),
        get_indication_expansion_templates(),
    ]


def get_all_templates() -> List[QueryTemplate]:
    """Get all templates from all libraries"""
    templates = []
    for library in get_all_template_libraries():
        templates.extend(library.get_all_templates())
    return templates


__all__ = [
    "QueryTemplate",
    "BaseTemplateLibrary",
    "ParameterExtractor",
    "DrugRepurposingTemplates",
    "get_drug_repurposing_templates",
    "TargetIdentificationTemplates",
    "get_target_identification_templates",
    "IndicationExpansionTemplates",
    "get_indication_expansion_templates",
    "get_all_template_libraries",
    "get_all_templates",
]

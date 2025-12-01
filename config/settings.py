"""
Configuration settings for QIAGEN BKB Text2Cypher Agent
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str
    neo4j_database: str = "neo4j"

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_temperature: float = 0.0

    # Agent Configuration
    max_iterations: int = 3
    query_timeout: int = 30
    enable_query_validation: bool = True
    enable_iterative_refinement: bool = True

    # Text2Cypher Configuration
    use_few_shot_examples: bool = True
    max_few_shot_examples: int = 5

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/text2cypher.log"

    # Optional: Alternative LLM Providers
    anthropic_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
def get_settings() -> Settings:
    """Get or create settings instance"""
    return Settings()


# Intent types for query classification
class QueryIntent:
    """Query intent categories"""
    DRUG_REPURPOSING = "drug_repurposing"
    TARGET_IDENTIFICATION = "target_identification"
    INDICATION_EXPANSION = "indication_expansion"
    PATHWAY_ANALYSIS = "pathway_analysis"
    DISEASE_DRUG_RELATION = "disease_drug_relation"
    BIOMARKER_DISCOVERY = "biomarker_discovery"
    DRUG_TARGET_INTERACTION = "drug_target_interaction"
    GENE_DISEASE_ASSOCIATION = "gene_disease_association"
    COMPOUND_SIMILARITY = "compound_similarity"
    GENERAL_QUERY = "general_query"  # Fallback to text2cypher


# QIAGEN BKB Node Types (based on research)
class BKBNodeTypes:
    """QIAGEN BKB node type constants"""
    DRUG = "Drug"
    COMPOUND = "Compound"
    GENE = "Gene"
    PROTEIN = "Protein"
    DISEASE = "Disease"
    PATHWAY = "Pathway"
    FUNCTION = "Function"
    BIOMARKER = "Biomarker"
    CELL_TYPE = "CellType"
    TISSUE = "Tissue"
    BIOLOGICAL_PROCESS = "BiologicalProcess"
    MOLECULAR_FUNCTION = "MolecularFunction"


# QIAGEN BKB Relationship Types
class BKBRelationshipTypes:
    """QIAGEN BKB relationship type constants"""
    TREATS = "TREATS"
    CAUSES = "CAUSES"
    TARGETS = "TARGETS"
    INTERACTS_WITH = "INTERACTS_WITH"
    ACTIVATES = "ACTIVATES"
    INHIBITS = "INHIBITS"
    UPREGULATES = "UPREGULATES"
    DOWNREGULATES = "DOWNREGULATES"
    BINDS_TO = "BINDS_TO"
    PARTICIPATES_IN = "PARTICIPATES_IN"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    REGULATES = "REGULATES"
    TRANSCRIBES = "TRANSCRIBES"
    PHOSPHORYLATES = "PHOSPHORYLATES"

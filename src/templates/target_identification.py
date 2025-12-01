"""
Predefined Cypher query templates for target identification
"""
from .base_templates import BaseTemplateLibrary, QueryTemplate
from config import QueryIntent


class TargetIdentificationTemplates(BaseTemplateLibrary):
    """Template library for target identification queries"""

    def _build_templates(self):
        """Build target identification query templates"""

        # Template 1: Find genes associated with disease
        self.templates.append(
            QueryTemplate(
                name="genes_for_disease",
                description="Find genes causally associated with a specific disease",
                cypher="""
                MATCH (disease:Disease {{name: $disease_name}})<-[rel:ASSOCIATED_WITH|CAUSES]-(gene:Gene)
                OPTIONAL MATCH (gene)-[:PARTICIPATES_IN]->(pathway:Pathway)
                WITH gene, rel, collect(DISTINCT pathway.name) as pathways
                RETURN gene.symbol as gene_symbol,
                       gene.name as gene_name,
                       gene.description as description,
                       type(rel) as association_type,
                       pathways,
                       gene.chromosome as chromosome
                ORDER BY gene.symbol
                LIMIT $limit
                """,
                parameters={"disease_name": str, "limit": int},
                intent=QueryIntent.TARGET_IDENTIFICATION,
                example_question="What genes are associated with breast cancer?",
                tags=[
                    "gene association",
                    "disease genes",
                    "target identification",
                    "genetic targets",
                ],
            )
        )

        # Template 2: Find protein targets for disease
        self.templates.append(
            QueryTemplate(
                name="proteins_for_disease",
                description="Find protein targets associated with a disease",
                cypher="""
                MATCH (disease:Disease {{name: $disease_name}})<-[:ASSOCIATED_WITH|CAUSES]-(gene:Gene)-[:TRANSCRIBES]->(protein:Protein)
                OPTIONAL MATCH (protein)-[:INTERACTS_WITH]->(interactor:Protein)
                WITH protein, gene, collect(DISTINCT interactor.name) as interacting_proteins
                OPTIONAL MATCH (drug:Drug)-[:TARGETS]->(protein)
                RETURN protein.name as protein_name,
                       protein.uniprot_id as uniprot_id,
                       protein.protein_class as protein_class,
                       gene.symbol as gene_symbol,
                       interacting_proteins,
                       collect(DISTINCT drug.name) as existing_drugs
                ORDER BY size(existing_drugs) DESC, protein.name
                LIMIT $limit
                """,
                parameters={"disease_name": str, "limit": int},
                intent=QueryIntent.TARGET_IDENTIFICATION,
                example_question="Find protein targets for Parkinson's disease",
                tags=[
                    "protein targets",
                    "disease proteins",
                    "therapeutic targets",
                    "druggable targets",
                ],
            )
        )

        # Template 3: Find targets in specific pathway
        self.templates.append(
            QueryTemplate(
                name="targets_in_pathway",
                description="Find druggable targets within a specific pathway",
                cypher="""
                MATCH (pathway:Pathway {{name: $pathway_name}})<-[:PARTICIPATES_IN]-(gene:Gene)
                OPTIONAL MATCH (drug:Drug)-[:TARGETS]->(gene)
                WITH gene, count(DISTINCT drug) as drug_count, collect(DISTINCT drug.name) as targeting_drugs
                RETURN gene.symbol as gene_symbol,
                       gene.name as gene_name,
                       gene.description as description,
                       drug_count,
                       targeting_drugs,
                       CASE WHEN drug_count > 0 THEN 'Drugged' ELSE 'Undrugged' END as target_status
                ORDER BY drug_count DESC, gene.symbol
                LIMIT $limit
                """,
                parameters={"pathway_name": str, "limit": int},
                intent=QueryIntent.TARGET_IDENTIFICATION,
                example_question="Find druggable targets in the MAPK signaling pathway",
                tags=[
                    "pathway targets",
                    "druggable genes",
                    "signaling pathway",
                    "target validation",
                ],
            )
        )

        # Template 4: Find biomarkers for disease
        self.templates.append(
            QueryTemplate(
                name="biomarkers_for_disease",
                description="Find biomarkers associated with a disease",
                cypher="""
                MATCH (disease:Disease {{name: $disease_name}})<-[:ASSOCIATED_WITH]-(biomarker:Biomarker)
                OPTIONAL MATCH (biomarker)-[:MEASURED_BY]->(gene:Gene)
                RETURN biomarker.name as biomarker_name,
                       biomarker.biomarker_type as biomarker_type,
                       collect(DISTINCT gene.symbol) as associated_genes,
                       biomarker.associated_diseases as diseases
                ORDER BY biomarker.name
                LIMIT $limit
                """,
                parameters={"disease_name": str, "limit": int},
                intent=QueryIntent.BIOMARKER_DISCOVERY,
                example_question="What are the biomarkers for lung cancer?",
                tags=[
                    "biomarkers",
                    "diagnostic markers",
                    "disease markers",
                    "prognostic markers",
                ],
            )
        )

        # Template 5: Find targets by tissue/cell type expression
        self.templates.append(
            QueryTemplate(
                name="targets_by_tissue_expression",
                description="Find genes highly expressed in specific tissue or cell type",
                cypher="""
                MATCH (tissue:Tissue {{name: $tissue_name}})<-[expr:EXPRESSED_IN]-(gene:Gene)
                WHERE expr.expression_level >= $min_expression_level
                OPTIONAL MATCH (gene)<-[:TARGETS]-(drug:Drug)
                OPTIONAL MATCH (gene)-[:ASSOCIATED_WITH]->(disease:Disease)
                RETURN gene.symbol as gene_symbol,
                       gene.name as gene_name,
                       expr.expression_level as expression_level,
                       collect(DISTINCT drug.name) as targeting_drugs,
                       collect(DISTINCT disease.name) as associated_diseases
                ORDER BY expr.expression_level DESC
                LIMIT $limit
                """,
                parameters={"tissue_name": str, "min_expression_level": float, "limit": int},
                intent=QueryIntent.TARGET_IDENTIFICATION,
                example_question="Find genes highly expressed in brain tissue",
                tags=[
                    "tissue expression",
                    "cell type",
                    "expression level",
                    "tissue-specific targets",
                ],
            )
        )

        # Template 6: Find novel undrugged targets for disease
        self.templates.append(
            QueryTemplate(
                name="undrugged_disease_targets",
                description="Find genes associated with disease that are not currently targeted by drugs",
                cypher="""
                MATCH (disease:Disease {{name: $disease_name}})<-[:ASSOCIATED_WITH|CAUSES]-(gene:Gene)
                WHERE NOT (gene)<-[:TARGETS]-(:Drug)
                OPTIONAL MATCH (gene)-[:PARTICIPATES_IN]->(pathway:Pathway)
                OPTIONAL MATCH (gene)-[:INTERACTS_WITH]-(interactor:Gene)<-[:TARGETS]-(drug:Drug)
                WITH gene,
                     collect(DISTINCT pathway.name) as pathways,
                     collect(DISTINCT {{interactor: interactor.symbol, drug: drug.name}}) as drugged_interactors
                RETURN gene.symbol as gene_symbol,
                       gene.name as gene_name,
                       gene.description as description,
                       pathways,
                       drugged_interactors,
                       size(drugged_interactors) as indirect_drugability_score
                ORDER BY indirect_drugability_score DESC, gene.symbol
                LIMIT $limit
                """,
                parameters={"disease_name": str, "limit": int},
                intent=QueryIntent.TARGET_IDENTIFICATION,
                example_question="Find novel undrugged targets for diabetes",
                tags=[
                    "undrugged targets",
                    "novel targets",
                    "drug discovery",
                    "target validation",
                ],
            )
        )


# Singleton instance
_target_id_templates = None


def get_target_identification_templates() -> TargetIdentificationTemplates:
    """Get or create target identification templates instance"""
    global _target_id_templates
    if _target_id_templates is None:
        _target_id_templates = TargetIdentificationTemplates()
    return _target_id_templates

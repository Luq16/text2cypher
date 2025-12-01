"""
Predefined Cypher query templates for drug repurposing
"""
from .base_templates import BaseTemplateLibrary, QueryTemplate
from config import QueryIntent


class DrugRepurposingTemplates(BaseTemplateLibrary):
    """Template library for drug repurposing queries"""

    def _build_templates(self):
        """Build drug repurposing query templates"""

        # Template 1: Find drugs with similar targets
        self.templates.append(
            QueryTemplate(
                name="similar_drugs_by_target",
                description="Find drugs that target similar genes/proteins as a reference drug",
                cypher="""
                MATCH (drug1:Drug {{name: $drug_name}})-[:TARGETS]->(target:Gene)
                MATCH (drug2:Drug)-[:TARGETS]->(target)
                WHERE drug1 <> drug2
                WITH drug2, collect(DISTINCT target.symbol) as shared_targets, count(DISTINCT target) as target_count
                WHERE target_count >= $min_shared_targets
                RETURN drug2.name as drug_name,
                       drug2.indication as current_indication,
                       shared_targets,
                       target_count,
                       drug2.mechanism as mechanism
                ORDER BY target_count DESC
                LIMIT $limit
                """,
                parameters={
                    "drug_name": str,
                    "min_shared_targets": int,
                    "limit": int,
                },
                intent=QueryIntent.DRUG_REPURPOSING,
                example_question="Find drugs with similar targets to Imatinib",
                tags=[
                    "similar drugs",
                    "shared targets",
                    "drug repurposing",
                    "similar mechanism",
                ],
            )
        )

        # Template 2: Find drugs for a new disease indication
        self.templates.append(
            QueryTemplate(
                name="drugs_for_disease_targets",
                description="Find existing drugs that target genes associated with a disease",
                cypher="""
                MATCH (disease:Disease {{name: $disease_name}})<-[:ASSOCIATED_WITH|CAUSES]-(gene:Gene)
                MATCH (drug:Drug)-[:TARGETS]->(gene)
                WITH drug, disease, collect(DISTINCT gene.symbol) as targeted_genes, count(DISTINCT gene) as gene_count
                OPTIONAL MATCH (drug)-[:TREATS]->(current_disease:Disease)
                RETURN drug.name as drug_name,
                       drug.indication as current_indication,
                       collect(DISTINCT current_disease.name) as current_diseases,
                       targeted_genes,
                       gene_count,
                       drug.mechanism as mechanism
                ORDER BY gene_count DESC
                LIMIT $limit
                """,
                parameters={"disease_name": str, "limit": int},
                intent=QueryIntent.DRUG_REPURPOSING,
                example_question="Find drugs that could be repurposed for Alzheimer's disease",
                tags=[
                    "drug repurposing",
                    "new indication",
                    "disease treatment",
                    "repurpose",
                ],
            )
        )

        # Template 3: Find drugs targeting specific pathway
        self.templates.append(
            QueryTemplate(
                name="drugs_targeting_pathway",
                description="Find drugs that target genes in a specific biological pathway",
                cypher="""
                MATCH (pathway:Pathway {{name: $pathway_name}})<-[:PARTICIPATES_IN]-(gene:Gene)
                MATCH (drug:Drug)-[:TARGETS|ACTIVATES|INHIBITS]->(gene)
                WITH drug, pathway, collect(DISTINCT gene.symbol) as pathway_genes, count(DISTINCT gene) as gene_count
                OPTIONAL MATCH (drug)-[r:TARGETS|ACTIVATES|INHIBITS]->(gene)
                RETURN drug.name as drug_name,
                       drug.indication as current_indication,
                       pathway_genes,
                       gene_count,
                       collect(DISTINCT type(r)) as interaction_types,
                       drug.mechanism as mechanism
                ORDER BY gene_count DESC
                LIMIT $limit
                """,
                parameters={"pathway_name": str, "limit": int},
                intent=QueryIntent.DRUG_REPURPOSING,
                example_question="Find drugs that target the PI3K/AKT signaling pathway",
                tags=[
                    "pathway",
                    "pathway targeting",
                    "drug repurposing",
                    "signaling",
                ],
            )
        )

        # Template 4: Find drugs with opposite mechanism for disease
        self.templates.append(
            QueryTemplate(
                name="drugs_with_inverse_mechanism",
                description="Find drugs that have opposite effect on disease-associated genes",
                cypher="""
                MATCH (disease:Disease {{name: $disease_name}})<-[:ASSOCIATED_WITH]-(gene:Gene)
                MATCH (gene)<-[causal:UPREGULATES|DOWNREGULATES]-(disease_entity)
                WITH gene, type(causal) as disease_effect
                MATCH (drug:Drug)-[drug_effect:UPREGULATES|DOWNREGULATES|ACTIVATES|INHIBITS]->(gene)
                WHERE (disease_effect = 'UPREGULATES' AND type(drug_effect) IN ['DOWNREGULATES', 'INHIBITS'])
                   OR (disease_effect = 'DOWNREGULATES' AND type(drug_effect) IN ['UPREGULATES', 'ACTIVATES'])
                WITH drug, collect(DISTINCT {{gene: gene.symbol, disease_effect: disease_effect, drug_effect: type(drug_effect)}}) as gene_effects
                RETURN drug.name as drug_name,
                       drug.indication as current_indication,
                       gene_effects,
                       size(gene_effects) as corrective_targets,
                       drug.mechanism as mechanism
                ORDER BY corrective_targets DESC
                LIMIT $limit
                """,
                parameters={"disease_name": str, "limit": int},
                intent=QueryIntent.DRUG_REPURPOSING,
                example_question="Find drugs that could correct the molecular changes in cancer",
                tags=[
                    "opposite mechanism",
                    "inverse effect",
                    "corrective therapy",
                    "repurposing",
                ],
            )
        )

        # Template 5: Find drugs by compound similarity
        self.templates.append(
            QueryTemplate(
                name="similar_compounds",
                description="Find drugs with similar chemical structure to a reference compound",
                cypher="""
                MATCH (compound1:Compound {{name: $compound_name}})
                MATCH (compound2:Compound)
                WHERE compound1 <> compound2
                  AND compound2.molecular_weight IS NOT NULL
                  AND abs(compound1.molecular_weight - compound2.molecular_weight) < $weight_tolerance
                WITH compound2,
                     abs(compound1.molecular_weight - compound2.molecular_weight) as weight_diff
                OPTIONAL MATCH (compound2)<-[:SIMILAR_TO]-(drug:Drug)
                OPTIONAL MATCH (drug)-[:TREATS]->(disease:Disease)
                RETURN compound2.name as compound_name,
                       compound2.molecular_weight as molecular_weight,
                       weight_diff,
                       collect(DISTINCT drug.name) as related_drugs,
                       collect(DISTINCT disease.name) as indications
                ORDER BY weight_diff ASC
                LIMIT $limit
                """,
                parameters={"compound_name": str, "weight_tolerance": float, "limit": int},
                intent=QueryIntent.COMPOUND_SIMILARITY,
                example_question="Find compounds similar to Metformin",
                tags=[
                    "compound similarity",
                    "chemical structure",
                    "similar compounds",
                    "molecular weight",
                ],
            )
        )


# Singleton instance
_drug_repurposing_templates = None


def get_drug_repurposing_templates() -> DrugRepurposingTemplates:
    """Get or create drug repurposing templates instance"""
    global _drug_repurposing_templates
    if _drug_repurposing_templates is None:
        _drug_repurposing_templates = DrugRepurposingTemplates()
    return _drug_repurposing_templates

"""
Predefined Cypher query templates for indication expansion
"""
from .base_templates import BaseTemplateLibrary, QueryTemplate
from config import QueryIntent


class IndicationExpansionTemplates(BaseTemplateLibrary):
    """Template library for indication expansion queries"""

    def _build_templates(self):
        """Build indication expansion query templates"""

        # Template 1: Find new indications for drug via targets
        self.templates.append(
            QueryTemplate(
                name="new_indications_via_targets",
                description="Find potential new disease indications for a drug based on its targets",
                cypher="""
                MATCH (drug:Drug {{name: $drug_name}})-[:TARGETS]->(target:Gene)
                MATCH (target)-[:ASSOCIATED_WITH|CAUSES]->(disease:Disease)
                OPTIONAL MATCH (drug)-[:TREATS]->(current_disease:Disease)
                WHERE NOT disease IN collect(current_disease)
                WITH disease, drug, collect(DISTINCT target.symbol) as shared_targets, count(DISTINCT target) as target_count
                OPTIONAL MATCH (disease)<-[:TREATS]-(competitor_drug:Drug)
                RETURN disease.name as disease_name,
                       disease.category as disease_category,
                       shared_targets,
                       target_count,
                       collect(DISTINCT competitor_drug.name) as existing_treatments,
                       size(collect(DISTINCT competitor_drug)) as treatment_count
                ORDER BY target_count DESC, treatment_count ASC
                LIMIT $limit
                """,
                parameters={"drug_name": str, "limit": int},
                intent=QueryIntent.INDICATION_EXPANSION,
                example_question="What new diseases could Metformin treat?",
                tags=[
                    "indication expansion",
                    "new indications",
                    "drug repurposing",
                    "new uses",
                ],
            )
        )

        # Template 2: Find indications via pathway overlap
        self.templates.append(
            QueryTemplate(
                name="indications_via_pathway",
                description="Find new indications for a drug based on pathway involvement",
                cypher="""
                MATCH (drug:Drug {{name: $drug_name}})-[:TARGETS|ACTIVATES|INHIBITS]->(gene:Gene)
                MATCH (gene)-[:PARTICIPATES_IN]->(pathway:Pathway)
                MATCH (pathway)<-[:PARTICIPATES_IN]-(disease_gene:Gene)-[:ASSOCIATED_WITH]->(disease:Disease)
                OPTIONAL MATCH (drug)-[:TREATS]->(current_disease:Disease)
                WHERE NOT disease IN collect(current_disease)
                WITH disease, pathway, drug,
                     collect(DISTINCT disease_gene.symbol) as disease_genes,
                     count(DISTINCT pathway) as pathway_count
                RETURN disease.name as disease_name,
                       disease.description as description,
                       collect(DISTINCT pathway.name) as shared_pathways,
                       pathway_count,
                       disease_genes
                ORDER BY pathway_count DESC
                LIMIT $limit
                """,
                parameters={"drug_name": str, "limit": int},
                intent=QueryIntent.INDICATION_EXPANSION,
                example_question="Find new indications for Imatinib based on pathway involvement",
                tags=[
                    "pathway overlap",
                    "indication expansion",
                    "shared pathways",
                    "mechanism overlap",
                ],
            )
        )

        # Template 3: Find related diseases for expansion
        self.templates.append(
            QueryTemplate(
                name="related_disease_indications",
                description="Find diseases related to current indication that drug might treat",
                cypher="""
                MATCH (drug:Drug {{name: $drug_name}})-[:TREATS]->(current_disease:Disease)
                MATCH (current_disease)<-[:ASSOCIATED_WITH]-(gene:Gene)-[:ASSOCIATED_WITH]->(related_disease:Disease)
                WHERE current_disease <> related_disease
                WITH related_disease, collect(DISTINCT gene.symbol) as shared_genes, count(DISTINCT gene) as gene_count
                OPTIONAL MATCH (related_disease)<-[:TREATS]-(existing_drug:Drug)
                RETURN related_disease.name as disease_name,
                       related_disease.category as disease_category,
                       related_disease.description as description,
                       shared_genes,
                       gene_count,
                       collect(DISTINCT existing_drug.name) as existing_treatments
                ORDER BY gene_count DESC
                LIMIT $limit
                """,
                parameters={"drug_name": str, "limit": int},
                intent=QueryIntent.INDICATION_EXPANSION,
                example_question="Find related diseases to expand indication for Aspirin",
                tags=[
                    "related diseases",
                    "disease similarity",
                    "indication expansion",
                    "comorbidities",
                ],
            )
        )

        # Template 4: Find indications via drug mechanism
        self.templates.append(
            QueryTemplate(
                name="indications_by_mechanism",
                description="Find diseases where drug's mechanism of action could be therapeutic",
                cypher="""
                MATCH (drug:Drug {{name: $drug_name}})-[effect:ACTIVATES|INHIBITS|UPREGULATES|DOWNREGULATES]->(target:Gene)
                MATCH (disease:Disease)<-[disease_rel:ASSOCIATED_WITH]-(target)
                OPTIONAL MATCH (drug)-[:TREATS]->(current_disease:Disease)
                WHERE NOT disease IN collect(current_disease)
                WITH disease, drug,
                     collect(DISTINCT {{
                         target: target.symbol,
                         drug_effect: type(effect),
                         disease_association: type(disease_rel)
                     }}) as mechanisms,
                     count(DISTINCT target) as target_count
                WHERE target_count >= $min_targets
                OPTIONAL MATCH (disease)<-[:TREATS]-(competitor:Drug)
                RETURN disease.name as disease_name,
                       disease.category as category,
                       mechanisms,
                       target_count,
                       collect(DISTINCT competitor.name) as competing_drugs
                ORDER BY target_count DESC
                LIMIT $limit
                """,
                parameters={"drug_name": str, "min_targets": int, "limit": int},
                intent=QueryIntent.INDICATION_EXPANSION,
                example_question="Find diseases where Rapamycin's mechanism could work",
                tags=[
                    "mechanism of action",
                    "drug mechanism",
                    "indication expansion",
                    "therapeutic mechanism",
                ],
            )
        )

        # Template 5: Find orphan disease opportunities
        self.templates.append(
            QueryTemplate(
                name="orphan_disease_opportunities",
                description="Find rare/orphan diseases with few treatments that drug might address",
                cypher="""
                MATCH (drug:Drug {{name: $drug_name}})-[:TARGETS]->(target:Gene)
                MATCH (target)-[:ASSOCIATED_WITH]->(disease:Disease)
                WHERE disease.category CONTAINS 'rare' OR disease.category CONTAINS 'orphan'
                OPTIONAL MATCH (disease)<-[:TREATS]-(existing_drug:Drug)
                WITH disease, drug,
                     collect(DISTINCT target.symbol) as drug_targets,
                     count(DISTINCT existing_drug) as treatment_count
                WHERE treatment_count < $max_existing_treatments
                RETURN disease.name as disease_name,
                       disease.description as description,
                       drug_targets,
                       size(drug_targets) as target_count,
                       treatment_count,
                       CASE WHEN treatment_count = 0 THEN 'Unmet Need' ELSE 'Limited Options' END as opportunity_type
                ORDER BY treatment_count ASC, target_count DESC
                LIMIT $limit
                """,
                parameters={"drug_name": str, "max_existing_treatments": int, "limit": int},
                intent=QueryIntent.INDICATION_EXPANSION,
                example_question="Find orphan disease opportunities for drug XYZ",
                tags=[
                    "orphan diseases",
                    "rare diseases",
                    "unmet need",
                    "indication expansion",
                ],
            )
        )

        # Template 6: Find indication expansion via biomarkers
        self.templates.append(
            QueryTemplate(
                name="indications_via_biomarkers",
                description="Find diseases with similar biomarker profiles for indication expansion",
                cypher="""
                MATCH (drug:Drug {{name: $drug_name}})-[:TREATS]->(current_disease:Disease)
                MATCH (current_disease)<-[:ASSOCIATED_WITH]-(biomarker:Biomarker)
                MATCH (biomarker)-[:ASSOCIATED_WITH]->(new_disease:Disease)
                WHERE current_disease <> new_disease
                WITH new_disease,
                     collect(DISTINCT biomarker.name) as shared_biomarkers,
                     count(DISTINCT biomarker) as biomarker_count
                OPTIONAL MATCH (new_disease)<-[:TREATS]-(competitor:Drug)
                RETURN new_disease.name as disease_name,
                       new_disease.category as category,
                       shared_biomarkers,
                       biomarker_count,
                       collect(DISTINCT competitor.name) as existing_treatments,
                       size(collect(DISTINCT competitor)) as treatment_count
                ORDER BY biomarker_count DESC, treatment_count ASC
                LIMIT $limit
                """,
                parameters={"drug_name": str, "limit": int},
                intent=QueryIntent.INDICATION_EXPANSION,
                example_question="Find indication expansion opportunities via biomarkers",
                tags=[
                    "biomarkers",
                    "biomarker overlap",
                    "indication expansion",
                    "precision medicine",
                ],
            )
        )


# Singleton instance
_indication_expansion_templates = None


def get_indication_expansion_templates() -> IndicationExpansionTemplates:
    """Get or create indication expansion templates instance"""
    global _indication_expansion_templates
    if _indication_expansion_templates is None:
        _indication_expansion_templates = IndicationExpansionTemplates()
    return _indication_expansion_templates

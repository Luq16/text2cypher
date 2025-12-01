"""
Few-shot examples for text2cypher generation
"""
from typing import List, Dict


class FewShotExamples:
    """Collection of few-shot examples for Cypher query generation"""

    @staticmethod
    def get_drug_discovery_examples() -> List[Dict[str, str]]:
        """
        Get few-shot examples for drug discovery domain

        Returns:
            List of question-cypher pairs
        """
        return [
            {
                "question": "What drugs target the EGFR gene?",
                "cypher": """MATCH (drug:Drug)-[:TARGETS]->(gene:Gene {symbol: 'EGFR'})
RETURN drug.name as drug_name, drug.indication as indication
LIMIT 10""",
            },
            {
                "question": "Find genes associated with breast cancer",
                "cypher": """MATCH (disease:Disease {name: 'Breast Cancer'})<-[:ASSOCIATED_WITH]-(gene:Gene)
RETURN gene.symbol as gene_symbol, gene.name as gene_name
LIMIT 20""",
            },
            {
                "question": "Which drugs treat Alzheimer's disease?",
                "cypher": """MATCH (drug:Drug)-[:TREATS]->(disease:Disease {name: "Alzheimer's Disease"})
RETURN drug.name as drug_name, drug.mechanism as mechanism
LIMIT 15""",
            },
            {
                "question": "Show me proteins that interact with TP53",
                "cypher": """MATCH (p1:Protein {name: 'TP53'})-[:INTERACTS_WITH]-(p2:Protein)
RETURN p2.name as protein_name, p2.protein_class as protein_class
LIMIT 20""",
            },
            {
                "question": "Find pathways involving MAPK signaling",
                "cypher": """MATCH (pathway:Pathway)
WHERE toLower(pathway.name) CONTAINS 'mapk'
OPTIONAL MATCH (pathway)<-[:PARTICIPATES_IN]-(gene:Gene)
RETURN pathway.name as pathway_name,
       collect(DISTINCT gene.symbol)[..10] as sample_genes
LIMIT 10""",
            },
            {
                "question": "What are the targets of Imatinib?",
                "cypher": """MATCH (drug:Drug {name: 'Imatinib'})-[:TARGETS]->(target)
RETURN target.symbol as target_symbol,
       target.name as target_name,
       labels(target) as target_type
LIMIT 20""",
            },
            {
                "question": "Find drugs that both activate and target genes in the PI3K pathway",
                "cypher": """MATCH (pathway:Pathway {name: 'PI3K Pathway'})<-[:PARTICIPATES_IN]-(gene:Gene)
MATCH (drug:Drug)-[r:TARGETS|ACTIVATES]->(gene)
RETURN drug.name as drug_name,
       collect(DISTINCT {gene: gene.symbol, relationship: type(r)}) as interactions
LIMIT 15""",
            },
            {
                "question": "Show diseases associated with BRCA1 or BRCA2 genes",
                "cypher": """MATCH (gene:Gene)-[:ASSOCIATED_WITH]->(disease:Disease)
WHERE gene.symbol IN ['BRCA1', 'BRCA2']
RETURN gene.symbol as gene,
       disease.name as disease_name,
       disease.category as category
LIMIT 20""",
            },
            {
                "question": "Find biomarkers for lung cancer",
                "cypher": """MATCH (disease:Disease {name: 'Lung Cancer'})<-[:ASSOCIATED_WITH]-(biomarker:Biomarker)
RETURN biomarker.name as biomarker_name,
       biomarker.biomarker_type as type
LIMIT 15""",
            },
            {
                "question": "Which drugs inhibit genes in the EGFR signaling pathway?",
                "cypher": """MATCH (pathway:Pathway {name: 'EGFR Signaling Pathway'})<-[:PARTICIPATES_IN]-(gene:Gene)
MATCH (drug:Drug)-[:INHIBITS]->(gene)
RETURN drug.name as drug_name,
       collect(DISTINCT gene.symbol) as inhibited_genes,
       drug.indication as current_indication
LIMIT 20""",
            },
            {
                "question": "Find genes highly expressed in brain tissue",
                "cypher": """MATCH (tissue:Tissue {name: 'Brain'})<-[expr:EXPRESSED_IN]-(gene:Gene)
WHERE expr.expression_level > 0.8
RETURN gene.symbol as gene_symbol,
       gene.name as gene_name,
       expr.expression_level as expression
ORDER BY expr.expression_level DESC
LIMIT 25""",
            },
            {
                "question": "What compounds are similar to Aspirin based on molecular weight?",
                "cypher": """MATCH (c1:Compound {name: 'Aspirin'})
MATCH (c2:Compound)
WHERE c2 <> c1
  AND abs(c1.molecular_weight - c2.molecular_weight) < 50
RETURN c2.name as compound_name,
       c2.molecular_weight as molecular_weight,
       abs(c1.molecular_weight - c2.molecular_weight) as weight_difference
ORDER BY weight_difference ASC
LIMIT 20""",
            },
        ]

    @staticmethod
    def get_advanced_examples() -> List[Dict[str, str]]:
        """
        Get advanced few-shot examples with complex queries

        Returns:
            List of question-cypher pairs
        """
        return [
            {
                "question": "Find drugs that could be repurposed for diabetes by targeting genes associated with the disease",
                "cypher": """MATCH (disease:Disease {name: 'Diabetes'})<-[:ASSOCIATED_WITH]-(gene:Gene)
MATCH (drug:Drug)-[:TARGETS]->(gene)
OPTIONAL MATCH (drug)-[:TREATS]->(current_disease:Disease)
WHERE current_disease.name <> 'Diabetes'
WITH drug,
     collect(DISTINCT gene.symbol) as targeted_genes,
     collect(DISTINCT current_disease.name) as current_indications
RETURN drug.name as drug_name,
       current_indications,
       targeted_genes,
       size(targeted_genes) as gene_count
ORDER BY gene_count DESC
LIMIT 15""",
            },
            {
                "question": "Find protein-protein interactions in the apoptosis pathway",
                "cypher": """MATCH (pathway:Pathway {name: 'Apoptosis Pathway'})<-[:PARTICIPATES_IN]-(gene:Gene)
MATCH (gene)-[:TRANSCRIBES]->(protein1:Protein)
MATCH (protein1)-[:INTERACTS_WITH]-(protein2:Protein)
MATCH (protein2)<-[:TRANSCRIBES]-(gene2:Gene)-[:PARTICIPATES_IN]->(pathway)
RETURN protein1.name as protein_1,
       protein2.name as protein_2,
       gene.symbol as gene_1,
       gene2.symbol as gene_2
LIMIT 30""",
            },
            {
                "question": "What are undrugged genes associated with cancer that have drugged interactors?",
                "cypher": """MATCH (disease:Disease {name: 'Cancer'})<-[:ASSOCIATED_WITH]-(gene:Gene)
WHERE NOT (gene)<-[:TARGETS]-(:Drug)
MATCH (gene)-[:INTERACTS_WITH]-(interactor:Gene)<-[:TARGETS]-(drug:Drug)
WITH gene,
     collect(DISTINCT {interactor: interactor.symbol, drug: drug.name}) as drugged_neighbors
RETURN gene.symbol as undrugged_gene,
       gene.name as gene_name,
       drugged_neighbors,
       size(drugged_neighbors) as drugability_score
ORDER BY drugability_score DESC
LIMIT 20""",
            },
        ]

    @staticmethod
    def get_all_examples() -> List[Dict[str, str]]:
        """Get all few-shot examples"""
        return (
            FewShotExamples.get_drug_discovery_examples()
            + FewShotExamples.get_advanced_examples()
        )

    @staticmethod
    def format_for_prompt(
        examples: List[Dict[str, str]], max_examples: int = 5
    ) -> str:
        """
        Format examples for inclusion in LLM prompt

        Args:
            examples: List of example dictionaries
            max_examples: Maximum number of examples to include

        Returns:
            Formatted string
        """
        formatted = ["# Example Cypher Queries:\n"]

        for i, example in enumerate(examples[:max_examples], 1):
            formatted.append(f"## Example {i}:")
            formatted.append(f"Question: {example['question']}")
            formatted.append(f"Cypher:\n{example['cypher']}\n")

        return "\n".join(formatted)

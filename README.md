# QIAGEN BKB Text2Cypher Agent

An intelligent AI agent for querying the QIAGEN Biomedical Knowledge Base (BKB) using natural language. The system implements a hybrid approach combining **predefined Cypher query templates** with **dynamic text2cypher generation** for maximum accuracy and flexibility.

## Features

- **Hybrid Query Approach**: Uses predefined templates for common patterns, falls back to text2cypher for novel queries
- **Intent Classification**: Automatically routes queries to appropriate handlers
- **Drug Discovery Focus**: Optimized for:
  - Drug repurposing
  - Target identification
  - Indication expansion
  - Pathway analysis
  - Biomarker discovery
- **Query Validation**: Automatic validation and refinement of generated Cypher queries
- **Natural Language Responses**: Synthesizes results into clear, informative answers
- **Interactive CLI**: User-friendly command-line interface
- **Extensible Architecture**: Easy to add new templates and query patterns

## Architecture

```
User Question
     ↓
Intent Classifier
     ↓
Query Router ─┬─→ Predefined Templates ──┐
              │                           ↓
              └─→ Text2Cypher Agent  ───→ Neo4j Execution
                                           ↓
                                    Result Synthesizer
                                           ↓
                                    Natural Language Answer
```

## Installation

### Prerequisites

- Python 3.9+
- Neo4j Database with QIAGEN BKB data
- OpenAI API key

### Setup

1. **Clone the repository**:
```bash
cd /Users/luqmanawoniyi_1/Documents/jazztext2cypher
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `NEO4J_URI`: Neo4j database URI (e.g., `bolt://localhost:7687`)
- `NEO4J_USERNAME`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `OPENAI_API_KEY`: Your OpenAI API key

### Neo4j Aura DB Setup

The system **fully supports Neo4j Aura** (cloud database). To use Aura:

1. **Get Aura credentials** from https://console.neo4j.io
2. **Use the secure URI format**:
   ```bash
   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-aura-generated-password
   NEO4J_DATABASE=neo4j
   ```

3. **Test your connection**:
   ```bash
   python test_aura_connection.py
   ```

**Key Notes for Aura:**
- Use `neo4j+s://` protocol (not `bolt://`)
- Password is auto-generated when creating the database
- Check firewall settings if connection fails
- Default database name is usually `neo4j`

See `.env.aura.example` for a complete Aura configuration template.

## Usage

### Interactive Mode

Launch the interactive CLI:

```bash
python -m src.main
```

Example session:
```
> What drugs target EGFR?
Processing query...
✓ Query successful!
  Query Type: template
  Intent: drug_target_interaction
  Results: 15

Answer:
Found 15 drugs that target EGFR including Gefitinib, Erlotinib, and Afatinib...

> Find genes associated with breast cancer
> suggest What are biomarkers for lung cancer?
> format json
> force-text2cypher on
```

### Single Query Mode

Execute a single query from command line:

```bash
# Natural language output
python -m src.main --query "Find drugs for Alzheimer's disease"

# JSON output
python -m src.main --query "What genes are associated with diabetes?" --format json

# Table format
python -m src.main --query "Show protein targets for cancer" --format table

# Force text2cypher
python -m src.main --query "Complex query" --force-text2cypher
```

### Programmatic Usage

```python
from src.main import BKBQueryAgent

# Initialize agent
agent = BKBQueryAgent()

# Single query
result = agent.query("Find drugs that could be repurposed for Parkinson's disease")

print(result['answer'])
print(f"Found {result['result_count']} results")
print(f"Query type: {result['query_type']}")  # 'template' or 'text2cypher'

# Batch queries
questions = [
    "What are biomarkers for lung cancer?",
    "Find genes in the MAPK pathway",
    "Which drugs inhibit TP53?"
]
results = agent.batch_query(questions)

# Get template suggestions
suggestions = agent.get_suggestions("Find similar drugs to Imatinib")
for sug in suggestions:
    print(f"{sug['name']}: {sug['description']}")
```

## Predefined Query Templates

The system includes 17+ optimized templates across three categories:

### Drug Repurposing Templates

- **similar_drugs_by_target**: Find drugs with similar targets
- **drugs_for_disease_targets**: Find drugs targeting disease-associated genes
- **drugs_targeting_pathway**: Find drugs affecting specific pathways
- **drugs_with_inverse_mechanism**: Find drugs with opposite effects
- **similar_compounds**: Find chemically similar compounds

### Target Identification Templates

- **genes_for_disease**: Find genes associated with diseases
- **proteins_for_disease**: Find protein targets for diseases
- **targets_in_pathway**: Find druggable targets in pathways
- **biomarkers_for_disease**: Find disease biomarkers
- **targets_by_tissue_expression**: Find tissue-specific targets
- **undrugged_disease_targets**: Find novel undrugged targets

### Indication Expansion Templates

- **new_indications_via_targets**: Find new indications based on targets
- **indications_via_pathway**: Find indications via pathway overlap
- **related_disease_indications**: Find related diseases for expansion
- **indications_by_mechanism**: Find indications matching drug mechanism
- **orphan_disease_opportunities**: Find orphan disease opportunities
- **indications_via_biomarkers**: Find indications via biomarker overlap

## Project Structure

```
jazztext2cypher/
├── src/
│   ├── agents/
│   │   ├── intent_classifier.py      # Query intent classification
│   │   ├── text2cypher_agent.py      # Dynamic Cypher generation
│   │   └── query_router.py           # Main routing logic
│   ├── templates/
│   │   ├── base_templates.py         # Base template classes
│   │   ├── drug_repurposing.py       # Drug repurposing queries
│   │   ├── target_identification.py  # Target discovery queries
│   │   └── indication_expansion.py   # Indication expansion queries
│   ├── utils/
│   │   ├── neo4j_connector.py        # Database connection
│   │   ├── schema_loader.py          # BKB schema management
│   │   ├── query_validator.py        # Query validation
│   │   └── result_synthesizer.py     # Natural language synthesis
│   ├── prompts/
│   │   ├── few_shot_examples.py      # Example queries for LLM
│   │   └── system_prompts.py         # LLM system prompts
│   └── main.py                        # CLI entry point
├── config/
│   ├── settings.py                    # Configuration management
│   └── bkb_schema.json               # QIAGEN BKB schema definition
├── tests/                             # Unit tests
├── examples/                          # Example notebooks
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
└── README.md                          # This file
```

## Configuration

Customize behavior in `config/settings.py` or via environment variables:

```python
# LLM Configuration
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.0

# Agent Configuration
MAX_ITERATIONS=3                # Max refinement attempts
QUERY_TIMEOUT=30                # Query timeout in seconds
ENABLE_QUERY_VALIDATION=true   # Validate queries before execution
ENABLE_ITERATIVE_REFINEMENT=true  # Enable query refinement on errors

# Text2Cypher Configuration
USE_FEW_SHOT_EXAMPLES=true     # Include examples in prompts
MAX_FEW_SHOT_EXAMPLES=5        # Number of examples to include
```

## QIAGEN BKB Schema

The system is configured for the QIAGEN Biomedical Knowledge Base with:

### Node Types
- Drug, Compound, Gene, Protein, Disease, Pathway, Function, Biomarker, Tissue, CellType, BiologicalProcess, MolecularFunction

### Relationship Types
- TREATS, CAUSES, TARGETS, INTERACTS_WITH, ACTIVATES, INHIBITS, UPREGULATES, DOWNREGULATES, BINDS_TO, PARTICIPATES_IN, ASSOCIATED_WITH, REGULATES, TRANSCRIBES, PHOSPHORYLATES, EXPRESSED_IN

### Statistics
- 600M+ total relationships
- 17,000 drugs
- 94,000 diseases
- 51,000 genes
- 1.48M causal relationships

## How It Works

### 1. Intent Classification

The system classifies queries into predefined intents:
- drug_repurposing
- target_identification
- indication_expansion
- pathway_analysis
- biomarker_discovery
- drug_target_interaction
- gene_disease_association
- compound_similarity
- general_query

### 2. Query Routing

Based on intent and keyword matching:
- **Matching template found** → Use optimized predefined query
- **No matching template** → Generate Cypher with text2cypher
- **Template execution fails** → Automatic fallback to text2cypher

### 3. Query Execution

- Validate Cypher syntax and schema compliance
- Execute against Neo4j database
- Handle errors with automatic refinement (up to 3 iterations)

### 4. Result Synthesis

- Convert Neo4j results to natural language
- Include context, statistics, and insights
- Format as natural language, JSON, or tables

## Examples

### Drug Repurposing

```python
query = "Find drugs similar to Imatinib that could be repurposed"
result = agent.query(query)
# Uses: similar_drugs_by_target template
# Returns: Drugs with shared tyrosine kinase targets
```

### Target Identification

```python
query = "What are undrugged targets for Alzheimer's disease?"
result = agent.query(query)
# Uses: undrugged_disease_targets template
# Returns: Novel genes associated with Alzheimer's not currently targeted
```

### Indication Expansion

```python
query = "What new diseases could Metformin treat?"
result = agent.query(query)
# Uses: new_indications_via_targets template
# Returns: Diseases with genes targeted by Metformin
```

### Text2Cypher Fallback

```python
query = "Find proteins that interact with TP53 in the apoptosis pathway"
result = agent.query(query)
# Uses: Text2Cypher (complex multi-hop query)
# Generates custom Cypher based on question
```

## Development

### Adding New Templates

1. Create template in appropriate file (e.g., `src/templates/drug_repurposing.py`)
2. Define QueryTemplate with:
   - Name and description
   - Parameterized Cypher query
   - Parameter types
   - Intent category
   - Example question
   - Matching keywords/tags

```python
self.templates.append(
    QueryTemplate(
        name="my_custom_query",
        description="Description of what this query does",
        cypher="""
        MATCH (d:Drug {{name: $drug_name}})-[:TARGETS]->(g:Gene)
        RETURN d.name, collect(g.symbol) as targets
        LIMIT $limit
        """,
        parameters={"drug_name": str, "limit": int},
        intent=QueryIntent.DRUG_TARGET_INTERACTION,
        example_question="Find targets of drug X",
        tags=["targets", "drug interaction"]
    )
)
```

### Running Tests

```bash
pytest tests/
```

## Troubleshooting

### Common Issues

1. **Connection Error**: Verify Neo4j is running and credentials are correct
2. **OpenAI API Error**: Check API key and rate limits
3. **No Results**: Verify BKB data is loaded in Neo4j
4. **Query Validation Fails**: Check schema compatibility

### Debug Mode

Enable verbose logging:

```bash
LOG_LEVEL=DEBUG python -m src.main
```

## Performance Considerations

- **Predefined templates**: ~100ms query time (optimized Cypher)
- **Text2Cypher**: ~2-5s query time (includes LLM call + generation)
- **Query validation**: Adds ~50ms overhead but prevents errors
- **Result synthesis**: ~1-2s for natural language generation

## Future Enhancements

- [ ] LangGraph-based multi-agent workflow
- [ ] Query result caching
- [ ] REST API with FastAPI
- [ ] Web UI dashboard
- [ ] Additional template libraries (toxicity, drug-drug interactions)
- [ ] Fine-tuned LLM for domain-specific Cypher generation
- [ ] Query history and learning from user feedback

## Contributing

To contribute:
1. Add templates in `src/templates/`
2. Update schema in `config/bkb_schema.json` if needed
3. Add tests in `tests/`
4. Update documentation

## License

MIT License - See LICENSE file for details

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{bkb_text2cypher,
  title={QIAGEN BKB Text2Cypher Agent},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/jazztext2cypher}
}
```

## Support

For issues and questions:
- GitHub Issues: [github.com/yourusername/jazztext2cypher/issues](https://github.com)
- Email: your.email@example.com

## Acknowledgments

- QIAGEN for the Biomedical Knowledge Base
- LangChain for the GraphCypherQAChain framework
- Neo4j for graph database technology
- OpenAI for GPT-4 language models

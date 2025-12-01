# Example Notebooks

This directory contains Jupyter notebooks demonstrating how to use the QIAGEN BKB Text2Cypher Agent.

## Available Notebooks

### 1. **getting_started.ipynb** ⭐ START HERE
A comprehensive step-by-step tutorial covering:
- ✅ Initial setup and connection
- ✅ First queries (drug discovery)
- ✅ Drug repurposing workflows
- ✅ Target identification
- ✅ Biomarker discovery
- ✅ Indication expansion
- ✅ Text2cypher for complex queries
- ✅ Batch processing
- ✅ Template suggestions
- ✅ Different output formats
- ✅ Intent classification
- ✅ Practice exercises

**Best for**: New users, learning the basics

### 2. **example_queries.ipynb**
Advanced examples and use cases:
- Complex multi-step queries
- Template exploration
- Intent classification deep dive
- Custom query patterns
- Performance comparisons

**Best for**: Advanced users, exploring specific use cases

## Quick Start

1. **Install dependencies**:
```bash
pip install -r ../requirements.txt
```

2. **Configure environment**:
```bash
cp ../.env.example ../.env
# Edit .env with your credentials
```

3. **Test connection** (for Aura DB):
```bash
python ../test_aura_connection.py
```

4. **Launch Jupyter**:
```bash
jupyter notebook
```

5. **Open** `getting_started.ipynb` and run cells sequentially

## Common Use Cases

### Drug Repurposing
```python
agent.query("Find drugs similar to Imatinib with at least 3 shared targets")
```

### Target Identification
```python
agent.query("What genes are associated with breast cancer?")
```

### Indication Expansion
```python
agent.query("What new diseases could Metformin treat?")
```

### Biomarker Discovery
```python
agent.query("What are biomarkers for lung cancer?")
```

### Complex Queries (Text2Cypher)
```python
agent.query("Find proteins that interact with TP53 in apoptosis pathway", force_text2cypher=True)
```

## Output Formats

### Natural Language (default)
```python
result = agent.query(question, format="natural")
print(result['answer'])
```

### JSON
```python
result = agent.query(question, format="json")
print(json.dumps(result['results'], indent=2))
```

### Table
```python
result = agent.query(question, format="table")
print(result['formatted_results'])
```

## Troubleshooting

### Connection Issues
- Verify `.env` configuration
- Run `python ../test_aura_connection.py`
- Check Neo4j/Aura DB is running

### Import Errors
- Ensure you're in the `examples/` directory
- Check `sys.path.append('..')` is in first cell
- Reinstall dependencies: `pip install -r ../requirements.txt`

### No Results
- Verify QIAGEN BKB data is loaded in Neo4j
- Check query syntax
- Try `force_text2cypher=True` for complex queries

## Need Help?

- 📖 Read the main [README.md](../README.md)
- 💬 Run interactive mode: `python -m src.main`
- 🔍 Get template suggestions: `agent.get_suggestions(your_question)`
- 🐛 Enable debug logging: Set `LOG_LEVEL=DEBUG` in `.env`

## Contributing

Found a useful query pattern? Add it to the examples!
1. Create a new cell in the notebook
2. Document the use case
3. Share your findings

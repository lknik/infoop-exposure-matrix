# InfoOp Exposure Matrix – Demo Classification System

This is a basic proof-of-concept web application implementing the FIMI (InfoOp) [Exposure Matrix](https://www.eeas.europa.eu/sites/default/files/documents/2025/EEAS-3nd-ThreatReport-March-2025-05-Digital-HD.pdf), a structured methodology designed to assess and classify digital media channels based on their potential involvement in disinformation and influence operations.

The system is inspired by the European External Action Service (EEAS) FIMI Exposure Matrix model and supports structured classification, indicator tracking, actor linkage, and basic analytical reporting powered by a local or remote large language model (LLM).

## Purpose and Scope

This demonstration system is intended for exploration and prototyping. It provides analysts and developers with a configurable and extensible foundation to:

- Simulate the assessment of suspected information operations.
- Test classification logic based on structured indicator inputs.
- Prototype integration with LLMs for generating analytical summaries.

## Features

### Operation and Channel Management

- Create and manage multiple information operations.
- Add multiple channels per operation, including social media accounts, websites, and other digital entities.
- Assign technical and behavioral indicators to channels, each with confidence levels and evidentiary details.

### Indicator Framework

- Indicators are categorized into technical and behavioral types.
- Each indicator includes:
  - Category and subtype
  - Confidence level (High, Medium, Low)
  - Weight (numeric impact on classification)
- Indicators can be customized, expanded, and persisted.

### Channel Relationships

- Define relationships between channels (e.g., coordination, reposting).
- Specify relationship type, confidence, and evidence.

### Automated Classification

- Channels are automatically scored and classified into one of four categories:
  - Official State Channel
  - State-Controlled Outlet
  - State-Linked Channel
  - State-Aligned Channel
- Classification is based on weighted indicators and predefined scoring thresholds.
- Includes output justification and confidence distribution.

### Exposure Matrix Visualization

- Channels are displayed in visual groupings based on classification.
- Visual emphasis on confidence and strength of attribution.

### LLM-Based Report Generation

- Generate natural-language operation summaries based on operation metadata and indicators.

## Installation and Setup

### Requirements

- Python 3.8 or higher
- pip (Python package manager)

### Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

Start the Flask server:

```bash
python app.py
```

Access the application via browser:

```
http://127.0.0.1:5000/
```
## Limitations

- This tool is for demonstration purposes only and is not production-ready.
- It uses a local SQLite database.
- Reporting accuracy depends on the quality and structure of provided indicators.
- LLM outputs are non-deterministic and may vary depending on model and prompt context.

## Future Work

- Graph-based visualizations of channel relationships.
- Multi-user support and access management.
- Indicator taxonomy editor and import/export.
- STIX support for interoperability.

## Author
Additional expert source in [my book](https://www.routledge.com/Propaganda-From-Disinformation-and-Influence-to-Operations-and-Information-Warfare/Olejnik/p/book/9781032813721)

me@lukaszolejnik.com

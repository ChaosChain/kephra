# Kephra: Autonomous Ethereum Core Dev Agents

Kephra is a system of autonomous AI agents designed to enhance Ethereum's governance process by automating key aspects of the EIP (Ethereum Improvement Proposal) lifecycle.

## Overview

Kephra transforms the Ethereum governance process through specialized AI agents that work together to identify, propose, review, and implement protocol improvements. By leveraging advanced language models and the Model Context Protocol (MCP), Kephra delivers:

- **Automated EIP generation** based on protocol metrics and community feedback
- **Technical review and validation** of proposals with extensive verification
- **Protocol simulation** to anticipate effects of changes on the network


## Architecture

Kephra consists of specialized AI agents, each with a specific role in the governance process:

1. **Proposer Agent**: Identifies needed improvements and creates well-structured EIPs
2. **Reviewer Agent**: Evaluates EIPs for technical correctness, standards compliance, and ecosystem impact
3. **Simulator/Tester Agent**: Implements and tests proposed changes in a safe environment
4. **Consensus Agent**: Aggregates reviews and test results to reach a final decision

## Autonomous Workflow with MCP

Kephra operates autonomously using the Model Context Protocol (MCP) servers, enabling seamless integration with GitHub, Git repositories, and the filesystem.

### MCP Servers Used

- **GitHub MCP Server**: Monitors repositories for issues and interacts with pull requests
- **Git MCP Server**: Manages EIP repositories, allowing agents to commit changes
- **Filesystem MCP Server**: Provides secure access to local files for code implementation and testing
- **Ethereum Validator Server**: Tests and validates protocol implementations

### Autonomous Pipeline

When running in autonomous mode, Kephra:

1. **Monitors GitHub** for issues that might need an EIP
2. **Analyzes protocol metrics** to identify improvement opportunities
3. **Generates EIPs** for suitable issues with complete technical specifications
4. **Reviews and evaluates** new and existing EIPs against standards
5. **Implements and tests** code changes required by EIPs
6. **Builds consensus** based on reviews and test results
7. **Submits changes** back to the appropriate repositories

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- Virtual environment (recommended)
- GitHub access token for API integration

### Initial Setup

1. Clone this repository:
```bash
git clone https://github.com/chaoschain/kephra.git
cd kephra
```

2. Create and activate a virtual environment:
```bash
python -m venv kenv
source kenv/bin/activate  # On Windows: kenv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your settings in the `.env` file:
```bash
cp .env.example .env
# Edit the .env file with your API keys and preferences
```

### Running Kephra

#### Start the Dashboard

The dashboard provides a visual interface to monitor and control Kephra:

```bash
python dashboard.py
```

Access the dashboard at http://localhost:8000

#### Run Autonomous Workflow

To run Kephra with the fully autonomous workflow:

```bash
python -m src.main --autonomous
```

## Dashboard Features

The dashboard allows you to:

- View active EIPs being worked on
- Monitor agent activities and logs in real-time
- Start and stop the Kephra system
- View GitHub issues being analyzed
- Track protocol metrics and insights

## Configuration

Key settings in the `.env` file include:

- `GITHUB_TOKEN`: Your GitHub access token
- `ISSUE_POLLING_INTERVAL`: How often to check for new issues (in seconds)
- `AUTONOMOUS_MODE`: Enable/disable autonomous workflow
- `ETH_NODE_URL`: Ethereum node URL for protocol metrics

## ChaosChain Integration

Kephra is designed as the first agent system to be deployed on ChaosChain, showcasing how autonomous AI agents can contribute to decentralized protocol development.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.


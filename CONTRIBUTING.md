# Contributing to Kephra

Thank you for your interest in contributing to Kephra! This document provides guidelines for contributing to this project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment following the instructions in the README.md

## Development Process

### Branching Strategy

- `main`: Stable release branch
- `develop`: Active development branch
- Feature branches: Named as `feature/your-feature-name`
- Bug fix branches: Named as `fix/bug-description`

Always create your working branches from `develop`.

### Pull Request Process

1. Ensure your code follows the project's style guidelines
2. Add or update tests as necessary
3. Ensure all tests pass locally before submitting your PR
4. Update documentation, including inline code comments
5. Submit your PR against the `develop` branch

## Agent Development Guidelines

### Creating New Agents

All agents should:
1. Inherit from the `KephraAgent` base class
2. Implement the required interface methods
3. Include comprehensive docstrings
4. Follow the established patterns for agent configuration and initialization

### Extending Existing Agents

- The `ReviewerAgent` can be extended for specialized review capabilities
- The `MCPEnhancedReviewerAgent` serves as an example of extending base agent functionality

## Code Style Guidelines

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Include type hints for all function parameters and return values
- Write comprehensive docstrings using Google style

## Testing

- Write unit tests for all new functionality
- Include integration tests for agent interactions
- Test with real EIP examples where possible

## Reporting Issues

Please use the GitHub issue tracker to report bugs or suggest features. When reporting issues:

1. Check if the issue already exists
2. Use a clear and descriptive title
3. Provide a detailed description of the issue
4. Include steps to reproduce the problem
5. Describe the expected behavior
6. Include any relevant logs or screenshots

## License

By contributing to Kephra, you agree that your contributions will be licensed under the project's MIT License. 
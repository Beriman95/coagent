# Contributing to CoAgent

Thank you for considering contributing to CoAgent! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

- **Clear title** describing the bug
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Environment details** (Python version, OS, etc.)
- **Logs or screenshots** if applicable

### Suggesting Features

Feature requests are welcome! Please:

- Check existing issues to avoid duplicates
- Clearly describe the feature and its benefits
- Explain use cases
- Consider implementation complexity

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages** (`git commit -m "Add amazing feature"`)
6. **Push to branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## 💻 Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/coagent.git
cd coagent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Run tests (when available)
pytest
```

## 📋 Code Style

### Python

- Follow **PEP 8** style guide
- Use **type hints** where applicable
- Write **docstrings** for functions and classes
- Keep functions focused and concise

**Example:**
```python
def search_documents(query: str, top_k: int = 5) -> list:
    """
    Search for relevant documents using hybrid search.
    
    Args:
        query: User's search query
        top_k: Number of results to return
        
    Returns:
        List of relevant documents with metadata
    """
    # Implementation
    pass
```

### Formatting

Use **Black** for Python code formatting:
```bash
pip install black
black .
```

### Linting

Use **flake8** for linting:
```bash
pip install flake8
flake8 . --max-line-length=120
```

## 🧪 Testing

- Write tests for new features
- Ensure existing tests pass
- Test edge cases and error handling

```bash
# Run tests
pytest

# With coverage
pytest --cov=.
```

## 📝 Commit Messages

Use clear, descriptive commit messages:

**Good:**
- `Add keyword matching to search function`
- `Fix hot-reload file watcher memory leak`
- `Update README with Docker instructions`

**Bad:**
- `Update file`
- `Fix bug`
- `Changes`

### Commit Message Format

```
<type>: <short description>

<detailed description if needed>

<issue reference if applicable>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## 🔍 Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation updated (if needed)
- [ ] No merge conflicts
- [ ] Commit messages are clear

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🎯 Areas for Contribution

### High Priority

- **Tests**: Expand test coverage
- **Documentation**: Improve guides and examples
- **Performance**: Optimize search and retrieval
- **Security**: Enhance security features

### Feature Ideas

- Multi-language support improvements
- Advanced analytics dashboard
- Automated testing suite
- CI/CD pipeline
- Performance benchmarks
- Kubernetes deployment guide

## 🚀 Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create release branch
4. Tag release (`git tag v1.0.0`)
5. Push tags (`git push --tags`)
6. Create GitHub release with notes

## 📚 Resources

- [Python Style Guide (PEP 8)](https://peps.python.org/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

## 💬 Questions?

Feel free to open an issue for:
- Questions about contributing
- Clarification on implementation
- Discussion of new features

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to CoAgent!** 🎉

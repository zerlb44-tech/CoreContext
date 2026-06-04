# Contributing

Contributions are welcome! Here's how to get started.

## Setup

```bash
git clone https://github.com/your-username/corecontext.git
cd corecontext
pip install -e .
pytest
```

## Making Changes

1. Create a branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Write tests for new functionality
4. Run tests: `PYTHONPATH=. pytest -v`
5. Commit with a clear message: `git commit -m "Add feature"`
6. Push and open a PR

## Guidelines

- Keep commits atomic and focused
- Write tests for all new features
- Update README if changing CLI interface
- Follow PEP 8 (we're lenient on 1-2 lines)
- No bare `except:` clauses

## Questions?

Open an issue or start a discussion.

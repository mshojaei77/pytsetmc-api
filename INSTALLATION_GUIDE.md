# PyTSETMC API Installation Guide

This guide provides step-by-step instructions for installing and using the PyTSETMC API package.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git (for GitHub installation)

## Installation Methods

### Method 1: Install from GitHub (Recommended)

This is the primary installation method for the PyTSETMC API package:

```bash
pip install git+https://github.com/mshojaei77/pytsetmc-api.git
```

#### For specific versions or branches:

```bash
# Install a specific version (tag)
pip install git+https://github.com/mshojaei77/pytsetmc-api.git@v0.1.0

# Install from a specific branch
pip install git+https://github.com/mshojaei77/pytsetmc-api.git@main

# Install from a specific commit
pip install git+https://github.com/mshojaei77/pytsetmc-api.git@commit-hash
```

### Method 2: Install from PyPI (Coming Soon)

Once published to PyPI, you'll be able to install with:

```bash
pip install pytsetmc-api
```

### Method 3: Development Installation

For developers who want to contribute or modify the package:

```bash
# Clone the repository
git clone https://github.com/mshojaei77/pytsetmc-api.git
cd pytsetmc-api

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Verification

After installation, verify that the package works correctly:

```python
import pytsetmc_api
print(f"PyTSETMC API version: {pytsetmc_api.__version__}")

# Test basic functionality
from pytsetmc_api import TSETMCClient
client = TSETMCClient()
print("Client initialized successfully!")
```

## Quick Start Example

```python
from pytsetmc_api import TSETMCClient

# Initialize the client
client = TSETMCClient()

# Search for a stock
stocks = client.search_stock("پترول")
print(f"Found {len(stocks)} stocks")

# Get stock information
if not stocks.empty:
    stock_info = client.get_stock_info("پترول")
    print(f"Stock: {stock_info.name}")
```

## Dependencies

The package automatically installs the following dependencies:

- pandas>=2.0.0
- numpy>=1.24.0
- requests>=2.31.0
- beautifulsoup4>=4.12.0
- aiohttp>=3.8.0
- jdatetime>=4.1.0
- persiantools>=4.0.0
- pydantic>=2.0.0
- rich>=13.0.0
- typer>=0.9.0
- unsync>=1.2.5
- lxml>=4.9.3
- html5lib>=1.1
- openpyxl>=3.1.2

## Optional Dependencies

For development and testing:

```bash
pip install pytsetmc-api[dev]
```

This includes:
- pytest>=7.4.0
- pytest-asyncio>=0.21.0
- pytest-cov>=4.1.0
- black>=23.7.0
- ruff>=0.0.280
- mypy>=1.5.0
- pre-commit>=3.3.0
- ipython>=8.12.0

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure Python 3.9+ is installed
2. **Network Issues**: Ensure you have internet access for GitHub installation
3. **Permission Issues**: Use `--user` flag if needed: `pip install --user git+https://github.com/mshojaei77/pytsetmc-api.git`

### Getting Help

- 📖 [Documentation](https://github.com/mshojaei77/pytsetmc-api#readme)
- 🐛 [Issue Tracker](https://github.com/mshojaei77/pytsetmc-api/issues)
- 💬 [Discussions](https://github.com/mshojaei77/pytsetmc-api/discussions)

## Uninstallation

To remove the package:

```bash
pip uninstall pytsetmc-api
```

## Next Steps

After successful installation, check out:

1. [README.md](README.md) for comprehensive usage examples
2. [API Documentation](https://github.com/mshojaei77/pytsetmc-api#api-reference)
3. [Example Scripts](main.py) for practical usage patterns 
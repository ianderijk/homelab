# List available recipes
default:
    @just --list --justfile {{justfile()}}

# Format Python code with ruff
format:
	uv run ruff format .

# Lint code with ruff
lint:
	uv run ruff check .

# Run static type checks
typecheck:
	uv run ty check

# Run format, lint, and typecheck
check: format lint typecheck

# Set up volume directories
setup-dirs:
    @echo 'Creating directories for Postgres, RustFS and PyPI'
    mkdir -p postgres_data rustfs_data pypi_packages
    @echo 'Created directories'

# Run the lakehouse CLI
homelab +args='--help':
    uv run ./lib/playground-cli/src/playground_cli/cli.py {{ args }}

# Initialize package setup
package name:
    uv run ./lib/package-setup/src/package_setup/setup.py {{ name }}

# Build package distribution archives
build name:
    uv build ./lib/{{ name }}

# Publish built package to the private index
publish name:
    uv publish ./lib/{{ name }}/dist/* --index homelab-index --username user --password password

# Install a package dependency from the private package index
install name:
    uv add {{ name }} --index-url http://127.0.0.1:8080/simple

# Run a service's main application
run name:
    mise exec -- uv run services/{{ name }}/main.py

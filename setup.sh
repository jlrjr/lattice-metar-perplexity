#!/bin/bash
# Setup script for METAR to Lattice Integration

echo "Setting up METAR to Lattice Integration..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create config file from template if it doesn't exist
if [ ! -f "config.yml" ]; then
    echo "Creating config.yml from template..."
    cp config_template.yml config.yml
    echo "Please edit config.yml with your Lattice credentials"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.yml with your Lattice credentials"
echo "2. Set environment variables:"
echo "   export LATTICE_URL='your-lattice-instance.com'"
echo "   export ENVIRONMENT_TOKEN='your-bearer-token'"
echo "   export SANDBOXES_TOKEN='your-sandbox-token'  # Optional"
echo "3. Run the integration:"
echo "   python metar_lattice_integration.py"

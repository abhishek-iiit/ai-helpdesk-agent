#!/bin/bash
# ============================================================
# AI IT Helpdesk Agent — Setup Script
# ============================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   AI IT Helpdesk Agent — Workshop Setup          ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION detected"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "→ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "→ Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY (required)"
    echo "   - LANGCHAIN_API_KEY (optional, for LangSmith)"
    echo "   - LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY (optional, for LangFuse)"
else
    echo "✓ .env already exists"
fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Setup Complete! Run the demo with:             ║"
echo "║                                                  ║"
echo "║   source .venv/bin/activate                      ║"
echo "║   python main.py --demo                          ║"
echo "║   python main.py --api     # Start API server    ║"
echo "║   python main.py           # Interactive CLI     ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

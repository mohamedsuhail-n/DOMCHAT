#!/bin/bash
set -e

echo "🔹 Updating system..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git build-essential

echo "🔹 Creating Python virtual environment..."
python3 -m venv dcenv
source dcenv/bin/activate

echo "🔹 Upgrading pip..."
pip install --upgrade pip wheel setuptools

echo "🔹 Installing Python dependencies..."
pip install -r requirements.txt

echo "🔹 Installing Playwright browsers..."
playwright install

echo "✅ Setup complete!"
echo ""
echo "👉 Next steps:"
echo "1. Activate your virtual environment: source dcenv/bin/activate"
echo "2. Make sure you have a .env file in the project root with:"
echo "   GROQ_API_KEY=your_api_key_here"
echo "3. Run the app with:"
echo "   python api.py"

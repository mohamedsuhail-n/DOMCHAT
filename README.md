# DOMCHAT 🤖

Domain Conversational Hub for Analytical Tasks

**Responsive AI for Domain Analysis & Reporting**

DOMCHAT is an intelligent web application that provides AI-powered domain analysis and reporting capabilities. Built with Python and Flask, it offers a responsive interface for comprehensive domain insights and analytics.

## 🚀 Features

- **AI-Powered Analysis**: Advanced domain analysis using artificial intelligence
- **Responsive Design**: Modern web interface that works across all devices
- **Real-time Reporting**: Generate comprehensive reports on domain data
- **Interactive Dashboard**: User-friendly interface for domain management
- **RESTful API**: Robust API endpoints for programmatic access
- **Playwright Integration**: Advanced web scraping and browser automation

## 🛠️ Tech Stack

- **Backend**: Python (71.2%)
- **Frontend**: JavaScript (16.8%), CSS (9.5%), HTML (2.0%)
- **Framework**: Flask
- **Web Automation**: Playwright
- **AI Integration**: Groq API
- **Deployment**: Shell scripts (0.5%)

## 📋 Prerequisites

- Ubuntu/Debian-based Linux system (recommended)
- Python 3.7+
- Git
- Sudo privileges for system package installation

## 🔧 Quick Installation

**One-command setup:**

1. **Clone and setup automatically**
   ```bash
   git clone https://github.com/mohamedsuhail-n/DOMCHAT.git
   cd DOMCHAT
   chmod +x setup.sh
   ./setup.sh
   ```

The setup script will automatically:
- ✅ Update your system packages
- ✅ Install Python 3, pip, venv, git, and build tools
- ✅ Create a Python virtual environment (`dcenv`)
- ✅ Install all Python dependencies
- ✅ Install Playwright browsers for web automation
- ✅ Set up the complete development environment

## 🔑 Configuration

**After installation, you need to:**

1. **Create environment file**
   ```bash
   touch .env
   ```

2. **Add your API key to `.env`**
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

3. **Review configuration**
   - Check `config.py` for additional settings
   - Modify as needed for your environment

## 🚀 Usage

1. **Activate the virtual environment**
   ```bash
   source dcenv/bin/activate
   ```

2. **Start the application**
   ```bash
   python api.py
   ```

3. **Access the web interface**
   - Open your browser and navigate to `http://localhost:5000`
   - Use the interactive dashboard to perform domain analysis

## 📁 Project Structure

```
DOMCHAT/
├── api.py              # Main Flask application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── setup.sh           # Automated setup script
├── .env               # Environment variables (create this)
├── dcenv/             # Python virtual environment
├── core/              # Core application logic
├── static/            # CSS, JS, and other static files
├── templates/         # HTML templates
└── README.md          # Project documentation
```

## 🔧 Manual Installation (Alternative)

If you prefer manual setup:

1. **Install system dependencies**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-pip python3-venv git build-essential
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv dcenv
   source dcenv/bin/activate
   ```

3. **Install Python packages**
   ```bash
   pip install --upgrade pip wheel setuptools
   pip install -r requirements.txt
   playwright install
   ```

## 🛠️ Development

**Activate environment for development:**
```bash
source dcenv/bin/activate
```

**Deactivate when done:**
```bash
deactivate
```

## 🔍 API Integration

This project uses the Groq API for AI-powered analysis. Make sure to:
- Sign up for a Groq API account
- Get your API key
- Add it to your `.env` file

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🚨 Troubleshooting

**Common issues:**

- **Permission errors**: Make sure you have sudo privileges
- **Virtual environment**: Always activate with `source dcenv/bin/activate`
- **Missing API key**: Ensure `.env` file exists with valid `GROQ_API_KEY`
- **Playwright issues**: Run `playwright install` if browsers aren't working

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Mohamed Suhail N**
- GitHub: [@mohamedsuhail-n](https://github.com/mohamedsuhail-n)

## 🙏 Acknowledgments

- Thanks to all contributors who have helped improve this project
- Groq API for AI capabilities
- Playwright team for browser automation tools
- Special thanks to the open-source community

## 📞 Support

If you have any questions or need help, please:
- Open an issue on GitHub
- Contact the maintainer

---

⭐ If you found this project helpful, please give it a star!

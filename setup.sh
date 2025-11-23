#!/bin/bash

# Network Security Tutor Bot - Setup Script
# This script sets up the complete environment

set -e

echo "🔐 Network Security Tutor & Quiz Bot - Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "📦 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version found"

# Check Node.js version
echo "📦 Checking Node.js version..."
node_version=$(node --version 2>&1)
echo "✅ Node.js $node_version found"

# Check if Ollama is installed
echo "📦 Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    
    # Check if Ollama service is running
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo "✅ Ollama service is running"
    else
        echo "⚠️  Ollama service is not running. Please start it with: ollama serve"
    fi
    
    # Check if llama3.2:3b is available
    if ollama list | grep -q "llama3.2:3b"; then
        echo "✅ Llama 3.2 3B model is installed"
    else
        echo "⚠️  Llama 3.2 3B model not found"
        echo "   Pulling model... (this may take a few minutes)"
        ollama pull llama3.2:3b
    fi
else
    echo "❌ Ollama is not installed. Please install it:"
    echo "   macOS: brew install ollama"
    echo "   Linux: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# Create virtual environment
echo ""
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python dependencies installed"

# Create directories
echo ""
echo "📁 Creating necessary directories..."
mkdir -p data/documents data/uploads data/chroma_db logs
echo "✅ Directories created"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created (you may want to customize it)"
else
    echo "✅ .env file already exists"
fi

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..
echo "✅ Frontend dependencies installed"

# Create sample document
echo ""
echo "📄 Creating sample network security document..."
cat > data/documents/sample_network_security.txt << 'EOF'
# Network Security Fundamentals

## Firewalls
A firewall is a network security device that monitors and controls incoming and outgoing network traffic based on predetermined security rules. Firewalls can be hardware-based, software-based, or a combination of both. They establish a barrier between trusted internal networks and untrusted external networks.

## Encryption
Encryption is the process of encoding information in such a way that only authorized parties can access it. There are two main types:
- Symmetric encryption: Uses the same key for encryption and decryption (e.g., AES)
- Asymmetric encryption: Uses a public key for encryption and a private key for decryption (e.g., RSA)

## DDoS Attacks
Distributed Denial of Service (DDoS) attacks attempt to make a network resource unavailable by overwhelming it with traffic from multiple sources. Common types include:
- Volume-based attacks (UDP floods, ICMP floods)
- Protocol attacks (SYN floods, Ping of Death)
- Application layer attacks (HTTP floods)

## VPN (Virtual Private Network)
A VPN creates a secure, encrypted connection over a less secure network, such as the internet. VPNs use tunneling protocols like IPSec, SSL/TLS, or WireGuard to ensure data privacy and security.

## Intrusion Detection Systems (IDS)
An IDS monitors network traffic for suspicious activity and known threats, generating alerts when potential security breaches are detected. IDS can be:
- Network-based (NIDS): Monitors entire network
- Host-based (HIDS): Monitors individual devices

## Authentication
Authentication verifies the identity of users or systems. Common methods include:
- Password-based authentication
- Multi-factor authentication (MFA)
- Biometric authentication
- Certificate-based authentication

## Common Network Attacks
- Man-in-the-Middle (MITM): Intercepting communication between two parties
- SQL Injection: Inserting malicious SQL code into applications
- Phishing: Social engineering attacks via email or messaging
- Zero-day exploits: Attacks exploiting unknown vulnerabilities

## Network Protocols
- TCP/IP: Fundamental protocol suite for internet communication
- HTTP/HTTPS: Web communication protocols
- SSH: Secure remote access protocol
- SSL/TLS: Cryptographic protocols for secure communication
EOF
echo "✅ Sample document created in data/documents/"

echo ""
echo "✨ Setup complete! "
echo ""
echo "📋 Next steps:"
echo "   1. Start Ollama (if not running): ollama serve"
echo "   2. Start the backend:"
echo "      cd backend"
echo "      python main.py"
echo "   3. In a new terminal, start the frontend:"
echo "      cd frontend"
echo "      npm run dev"
echo "   4. Open http://localhost:3000 in your browser"
echo ""
echo "📚 Upload more documents in the Documents tab or place them in data/documents/"
echo ""
echo "🎉 Happy learning!"

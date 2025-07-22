#!/usr/bin/env python3
"""
Temporal Workflow Orchestration System - Main Startup Script
Simplified startup that launches the Flask web application directly.

Usage:
    python start.py                    # Start the web application
    python start.py --host 0.0.0.0    # Start with custom host
    python start.py --port 8080       # Start with custom port
    python start.py --debug           # Start in debug mode
"""

import sys
import os
import argparse
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Set environment variables
os.environ['GROQ_API_KEY_PROD4'] = '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'

def print_banner():
    """Print startup banner"""
    print("=" * 80)
    print("🚀 TEMPORAL WORKFLOW ORCHESTRATION SYSTEM")
    print("   7-Service Architecture with LLM Integration")
    print("=" * 80)
    print()
    
def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Temporal Workflow Orchestration System"
    )
    parser.add_argument(
        '--host', 
        default='0.0.0.0', 
        help='Host to bind the server to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000, 
        help='Port to bind the server to (default: 5000)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Run in debug mode'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    try:
        # Import Flask app from the workflow-ui module
        from flask import Flask, render_template_string, request, jsonify
        from flask_cors import CORS
        from services.updated_services import ServiceRegistry
        from services.groq_service import GroqLLMService
        
        # Import the main app
        sys.path.insert(0, str(Path(__file__).parent / "app"))
        from main import app
        
        print(f"🌐 Starting Flask Web UI on http://{args.host}:{args.port}")
        print("📋 Available Services:")
        
        # Show available services
        registry = ServiceRegistry()
        services = registry.list_services()
        for name, description in services.items():
            service = registry.get_service(name)
            service_type = "🌐 REAL API" if "Currency" in service.__class__.__name__ else "🤖 DUMMY"
            failure_rate = getattr(service, 'failure_rate', 0) * 100
            print(f"   {service_type} {name} (Failure Rate: {failure_rate:.1f}%)")
        
        print("\n✨ System ready! Open your browser and start creating workflows!")
        print(f"🔗 Access the UI at: http://localhost:{args.port}")
        print("\n💡 Try these example workflows:")
        print("   • 'Order 2 laptops for our office team'")
        print("   • 'Book a flight from NYC to Paris for business'")
        print("   • 'Purchase enterprise software licenses'")
        print("\n⚠️  Press Ctrl+C to stop the server")
        print("-" * 80)
        
        # Start the Flask application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install flask flask-cors temporalio groq")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
OppNDA - Entry Point
Cross-platform compatible launcher for the web interface.

Usage:
    pip install -r requirements.txt      # Install dependencies
    python OppNDA.py                     # Start on default port 5001
    python OppNDA.py --port 8080         # Start on custom port
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description='OppNDA Web Interface')
    parser.add_argument('--port', type=int, default=5001, help='Port to run on (default: 5001)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Import and run app
    try:
        from app import create_app
    except ImportError as e:
        print(f"Error importing app: {e}")
        print(f"Project root added to path: {PROJECT_ROOT}")
        sys.exit(1)
    
    app = create_app()
    
    print("""
============================================================
                  OppNDA Web Interface                      
============================================================
  Usage:
    python OppNDA.py                  Start on default port 5001
    python OppNDA.py --port 8080      Start on custom port
    python OppNDA.py --host 0.0.0.0   Bind to all interfaces
    python OppNDA.py --debug          Enable debug mode
  
  Press Ctrl+C to stop the server
============================================================
""")
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()

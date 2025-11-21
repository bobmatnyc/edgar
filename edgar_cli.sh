#!/bin/bash
# EDGAR CLI Launcher Script
# Starts interactive mode by default

cd "/Users/masa/Clients/Zach/projects/edgar"
source venv/bin/activate
python -m edgar_analyzer "$@"

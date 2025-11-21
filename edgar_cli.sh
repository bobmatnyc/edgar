#!/bin/bash
# EDGAR CLI Launcher Script
# Starts interactive mode by default
# Use --cli flag to bypass interactive mode and see CLI help

cd "/Users/masa/Clients/Zach/projects/edgar"
source venv/bin/activate
edgar-analyzer "$@"

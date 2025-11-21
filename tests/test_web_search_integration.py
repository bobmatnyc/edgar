#!/usr/bin/env python3
"""
Script Name: test_web_search_integration.py

PURPOSE:
    Test the web search integration with OpenRouter for the CLI Chatbot Controller,
    LLM Supervisor, and LLM Engineer components.

FUNCTION:
    Web search capability testing:
    - Tests OpenRouter web search standard integration
    - Validates LLM service web search functionality
    - Tests supervisor validation with web search
    - Tests engineer best practices search
    - Demonstrates CLI controller with web search

USAGE:
    python test_web_search_integration.py [options]
    
    Arguments:
        --test-llm-service: Test LLM service web search
        --test-supervisor: Test supervisor with web search validation
        --test-engineer: Test engineer with best practices search
        --test-controller: Test CLI controller with web search
        --test-all: Run all web search tests
    
    Examples:
        python test_web_search_integration.py --test-all
        python test_web_search_integration.py --test-llm-service
        python test_web_search_integration.py --test-controller

MODIFICATION HISTORY:
    2025-11-21 System - Initial creation
    - WHY: Need to test web search integration across all components
    - HOW: Comprehensive testing of OpenRouter web search capabilities
    - IMPACT: Validates web search functionality for real-time information access

DEPENDENCIES:
    - Python 3.8+
    - OpenRouter API key configured
    - All EDGAR CLI components

AUTHOR: EDGAR CLI System
CREATED: 2025-11-21
LAST_MODIFIED: 2025-11-21
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import structlog
from edgar_analyzer.services.llm_service import LLMService
from self_improving_code.llm.supervisor import LLMSupervisor
from self_improving_code.llm.engineer import LLMEngineer
from cli_chatbot.core.controller import ChatbotController

logger = structlog.get_logger(__name__)


async def test_llm_service_web_search():
    """Test LLM service web search capabilities."""
    print("\n🔍 Testing LLM Service Web Search")
    print("=" * 50)
    
    try:
        # Initialize LLM service
        llm_service = LLMService()
        
        # Test basic web search
        print("📊 Testing basic web search...")
        result = await llm_service.web_search_request(
            query="SEC executive compensation disclosure requirements 2024",
            context="Validating current regulatory requirements",
            max_results=3
        )
        
        print(f"✅ Web search result (first 200 chars):")
        print(f"   {result[:200]}...")
        
        # Test enhanced analysis with search
        print("\n📈 Testing enhanced analysis with web search...")
        sample_compensation_data = """
        CEO: John Smith - Total: $5,000,000
        CFO: Jane Doe - Total: $3,000,000
        """
        
        enhanced_result = await llm_service.enhanced_analysis_with_search(
            primary_content=sample_compensation_data,
            search_queries=[
                "average CEO compensation 2024",
                "executive compensation benchmarks"
            ],
            analysis_prompt="Analyze this compensation data against current market standards",
            context="Executive compensation analysis"
        )
        
        print(f"✅ Enhanced analysis result (first 300 chars):")
        print(f"   {enhanced_result[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM service web search test failed: {e}")
        return False


async def test_supervisor_web_search():
    """Test LLM Supervisor with web search validation."""
    print("\n🔍 Testing LLM Supervisor Web Search Validation")
    print("=" * 50)
    
    try:
        # Initialize LLM service for web search
        llm_service = LLMService()
        
        async def llm_client(messages):
            return await llm_service._make_llm_request(messages)
        
        async def web_search_client(query, context=None):
            return await llm_service.web_search_request(query, context)
        
        # Initialize supervisor with web search
        supervisor = LLMSupervisor(
            llm_client=llm_client,
            enable_web_search=True,
            web_search_client=web_search_client,
            domain_expertise="executive compensation analysis"
        )
        
        # Test evaluation with web search validation
        print("📊 Testing supervisor evaluation with web search...")
        
        test_results = {
            "compensations": [
                {"name": "CEO", "total": 15000000},
                {"name": "CFO", "total": 8000000}
            ],
            "extraction_method": "automated_parsing",
            "data_quality": "high"
        }
        
        evaluation = await supervisor.evaluate_results(
            test_results=test_results,
            iteration=1,
            context={
                "domain": "executive compensation analysis",
                "requirements": "accurate SEC filing data extraction"
            },
            enable_search_for_validation=True
        )
        
        print(f"✅ Supervisor evaluation with web search:")
        print(f"   Quality Score: {evaluation.get('quality_score', 'N/A')}")
        print(f"   QA Status: {evaluation.get('qa_status', 'N/A')}")
        print(f"   Issues Found: {len(evaluation.get('issues_found', []))}")
        print(f"   Web Search Used: {'Yes' if 'web search' in str(evaluation).lower() else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supervisor web search test failed: {e}")
        return False


async def test_engineer_web_search():
    """Test LLM Engineer with best practices search."""
    print("\n🔍 Testing LLM Engineer Best Practices Search")
    print("=" * 50)
    
    try:
        # Initialize LLM service for web search
        llm_service = LLMService()
        
        async def llm_client(messages):
            return await llm_service._make_llm_request(messages)
        
        async def web_search_client(query, context=None):
            return await llm_service.web_search_request(query, context)
        
        # Initialize engineer with web search
        engineer = LLMEngineer(
            llm_client=llm_client,
            enable_web_search=True,
            web_search_client=web_search_client,
            programming_language="Python"
        )
        
        # Test implementation with best practices search
        print("🛠️  Testing engineer implementation with best practices search...")
        
        evaluation = {
            "needs_improvement": True,
            "issues_found": ["performance optimization needed", "error handling insufficient"],
            "improvement_directions": ["optimize data processing", "add comprehensive error handling"]
        }
        
        test_results = {"processing_time": 5.2, "errors": 2}
        current_code = {"main.py": "def process_data(): pass"}
        
        implementation = await engineer.implement_improvements(
            evaluation=evaluation,
            test_results=test_results,
            current_code=current_code,
            context={
                "domain": "data processing",
                "requirements": "high performance data extraction"
            },
            enable_search_for_best_practices=True
        )
        
        print(f"✅ Engineer implementation with web search:")
        print(f"   Changes Made: {implementation.get('changes_made', 'N/A')}")
        print(f"   Files Modified: {len(implementation.get('files_modified', []))}")
        print(f"   Summary: {implementation.get('summary', 'N/A')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Engineer web search test failed: {e}")
        return False


async def test_controller_web_search():
    """Test CLI Controller with web search capabilities."""
    print("\n🔍 Testing CLI Controller Web Search Integration")
    print("=" * 50)
    
    try:
        # Initialize LLM service
        llm_service = LLMService()
        
        async def llm_client(messages):
            return await llm_service._make_llm_request(messages)
        
        async def web_search_client(query, context=None):
            return await llm_service.web_search_request(query, context)
        
        # Initialize controller with web search
        controller = ChatbotController(
            llm_client=llm_client,
            application_root=str(Path(__file__).parent),
            web_search_enabled=True,
            web_search_client=web_search_client
        )
        
        print("✅ CLI Controller initialized with web search capabilities")
        print(f"   Web Search Enabled: {controller.web_search_enabled}")
        print(f"   Web Search Client: {'Available' if controller.web_search_client else 'Not Available'}")
        
        # Test would require full conversation loop, so just validate initialization
        return True
        
    except Exception as e:
        print(f"❌ Controller web search test failed: {e}")
        return False


async def main():
    """Main test execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test EDGAR CLI web search integration")
    parser.add_argument("--test-llm-service", action="store_true", help="Test LLM service web search")
    parser.add_argument("--test-supervisor", action="store_true", help="Test supervisor web search")
    parser.add_argument("--test-engineer", action="store_true", help="Test engineer web search")
    parser.add_argument("--test-controller", action="store_true", help="Test controller web search")
    parser.add_argument("--test-all", action="store_true", help="Run all web search tests")
    
    args = parser.parse_args()
    
    if not any([args.test_llm_service, args.test_supervisor, args.test_engineer, 
                args.test_controller, args.test_all]):
        args.test_all = True
    
    print("🚀 EDGAR CLI Web Search Integration Testing")
    print("=" * 60)
    print("TESTING WEB SEARCH CAPABILITIES:")
    print("• OpenRouter web search standard integration")
    print("• LLM service web search functionality")
    print("• Supervisor validation with real-time information")
    print("• Engineer best practices search")
    print("• CLI controller web search integration")
    print("=" * 60)
    
    results = {}
    
    try:
        if args.test_all or args.test_llm_service:
            results['llm_service'] = await test_llm_service_web_search()
        
        if args.test_all or args.test_supervisor:
            results['supervisor'] = await test_supervisor_web_search()
        
        if args.test_all or args.test_engineer:
            results['engineer'] = await test_engineer_web_search()
        
        if args.test_all or args.test_controller:
            results['controller'] = await test_controller_web_search()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 WEB SEARCH INTEGRATION TEST COMPLETE")
        print("=" * 60)
        
        print("📊 **TEST RESULTS:**")
        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {test_name.title()}: {status}")
        
        overall_success = all(results.values())
        print(f"\n🎯 **OVERALL STATUS:** {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if overall_success:
            print("\n🚀 **WEB SEARCH CAPABILITIES READY:**")
            print("   • Real-time information access for validation")
            print("   • Current best practices search for improvements")
            print("   • Enhanced analysis with web search context")
            print("   • OpenRouter web search standard integration")
        
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

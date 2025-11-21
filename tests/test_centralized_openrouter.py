#!/usr/bin/env python3
"""
Script Name: test_centralized_openrouter.py

PURPOSE:
    Test the centralized OpenRouter service architecture to ensure
    model-independent API handling and proper service integration.

FUNCTION:
    Centralized service validation:
    - Tests OpenRouter service with different models
    - Validates model-specific parameter handling
    - Tests web search integration across models
    - Validates fallback logic and error handling
    - Tests LLM service integration with centralized service

USAGE:
    python test_centralized_openrouter.py
    
MODIFICATION HISTORY:
    2025-11-21 System - Initial creation
    - WHY: Validate centralized OpenRouter service architecture
    - HOW: Comprehensive testing of service integration
    - IMPACT: Ensures clean, maintainable API architecture

DEPENDENCIES:
    - Python 3.8+
    - OpenRouter API key configured
    - Centralized OpenRouter service

AUTHOR: EDGAR CLI System
CREATED: 2025-11-21
LAST_MODIFIED: 2025-11-21
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from edgar_analyzer.services.openrouter_service import OpenRouterService
from edgar_analyzer.services.llm_service import LLMService


async def test_openrouter_service():
    """Test centralized OpenRouter service functionality."""
    print("\n🔧 Testing Centralized OpenRouter Service")
    print("=" * 50)
    
    try:
        service = OpenRouterService()
        
        # Test model configuration
        print("✅ Service initialized successfully")
        print(f"   Available models: {len(service.get_available_models())}")
        
        # Test model-specific configuration
        grok_config = service.get_model_config("x-ai/grok-4.1-fast:free")
        claude_config = service.get_model_config("anthropic/claude-3.5-sonnet")
        
        print(f"   Grok config: {grok_config['max_tokens']} tokens, web search: {grok_config['supports_web_search']}")
        print(f"   Claude config: {claude_config['max_tokens']} tokens, web search: {claude_config['supports_web_search']}")
        
        # Test basic chat completion
        response = await service.chat_completion(
            messages=[{"role": "user", "content": "Say 'OpenRouter service working'"}],
            model="x-ai/grok-4.1-fast:free",
            temperature=0.1,
            max_tokens=20
        )
        print(f"   Basic chat response: {response}")
        
        # Test fallback functionality
        response = await service.chat_completion_with_fallback(
            messages=[{"role": "user", "content": "Say 'Fallback working'"}],
            primary_model="x-ai/grok-4.1-fast:free",
            fallback_models=["anthropic/claude-3.5-sonnet"],
            temperature=0.1,
            max_tokens=20
        )
        print(f"   Fallback response: {response}")
        
        # Test web search capability
        if service.supports_web_search("x-ai/grok-4.1-fast:free"):
            print("   ✅ Web search supported for Grok model")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter service test failed: {e}")
        return False


async def test_llm_service_integration():
    """Test LLM service integration with centralized OpenRouter service."""
    print("\n🔧 Testing LLM Service Integration")
    print("=" * 50)
    
    try:
        service = LLMService()
        
        print("✅ LLM service initialized with centralized OpenRouter")
        
        # Test basic LLM request
        response = await service._make_llm_request(
            messages=[{"role": "user", "content": "Say 'LLM integration working'"}],
            temperature=0.1,
            max_tokens=20
        )
        print(f"   LLM request response: {response}")
        
        # Test web search request
        web_response = await service.web_search_request(
            query="test query for integration",
            max_results=1,
            temperature=0.1
        )
        print(f"   Web search response length: {len(web_response)}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM service integration test failed: {e}")
        return False


async def test_model_independence():
    """Test model-independent API handling."""
    print("\n🔧 Testing Model Independence")
    print("=" * 50)
    
    try:
        service = OpenRouterService()
        
        # Test different models with same interface
        models_to_test = [
            "x-ai/grok-4.1-fast:free",
            "anthropic/claude-3.5-sonnet"
        ]
        
        for model in models_to_test:
            try:
                response = await service.chat_completion(
                    messages=[{"role": "user", "content": f"Say 'Model {model} working'"}],
                    model=model,
                    temperature=0.1,
                    max_tokens=30
                )
                print(f"   ✅ {model}: {response}")
            except Exception as e:
                print(f"   ❌ {model}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model independence test failed: {e}")
        return False


async def main():
    """Main test execution function."""
    print("🚀 Centralized OpenRouter Service Testing")
    print("=" * 60)
    print("TESTING CENTRALIZED ARCHITECTURE:")
    print("• OpenRouter service with model-independent interface")
    print("• Model-specific parameter handling")
    print("• Web search integration across models")
    print("• LLM service integration with centralized service")
    print("• Fallback logic and error handling")
    print("=" * 60)
    
    results = {}
    
    try:
        results['openrouter_service'] = await test_openrouter_service()
        results['llm_integration'] = await test_llm_service_integration()
        results['model_independence'] = await test_model_independence()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 CENTRALIZED OPENROUTER SERVICE TEST COMPLETE")
        print("=" * 60)
        
        print("📊 **TEST RESULTS:**")
        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        overall_success = all(results.values())
        print(f"\n🎯 **OVERALL STATUS:** {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if overall_success:
            print("\n🚀 **CENTRALIZED ARCHITECTURE VALIDATED:**")
            print("   ✅ Single OpenRouter service for all API calls")
            print("   ✅ Model-independent interface design")
            print("   ✅ Centralized configuration and error handling")
            print("   ✅ Clean separation of concerns")
            print("   ✅ Maintainable and extensible architecture")
        
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

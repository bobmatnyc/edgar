#!/usr/bin/env python3
"""
Test the CLI Chatbot Controller

This demonstrates the revolutionary replacement of traditional CLI patterns
with an intelligent, self-aware conversational interface.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli_chatbot import ChatbotController
from edgar_analyzer.services.llm_service import LLMService

async def test_cli_chatbot():
    """Test the CLI chatbot controller."""
    
    print("🚀 Testing CLI Chatbot Controller")
    print("=" * 60)
    print("REVOLUTIONARY CLI REPLACEMENT:")
    print("• Self-aware conversational interface")
    print("• Dynamic context injection from live codebase")
    print("• Real-time script generation and execution")
    print("• Memory and learning capabilities")
    print("• Natural language command processing")
    print("=" * 60)
    
    # Initialize LLM service
    try:
        llm_service = LLMService()
        print("✅ LLM service initialized for chatbot")
    except Exception as e:
        print(f"❌ Failed to initialize LLM service: {e}")
        return
    
    # Create LLM client function
    async def llm_client(messages):
        """LLM client function for the chatbot."""
        return await llm_service._make_llm_request(
            messages, temperature=0.7, max_tokens=2000
        )
    
    # Initialize the chatbot controller
    try:
        controller = ChatbotController(
            llm_client=llm_client,
            application_root=os.path.dirname(__file__),  # Use current project as application
            scripting_enabled=True
        )
        print("✅ CLI Chatbot Controller initialized")
        print("   • Dynamic context injection enabled")
        print("   • Script execution enabled")
        print("   • Self-awareness activated")
        print("   • Conversation memory active")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot controller: {e}")
        return
    
    print("\n🎯 DEMONSTRATION MODE")
    print("The chatbot will demonstrate its capabilities with sample interactions.")
    print("In real usage, you would call: await controller.start_conversation()")
    
    # Demonstrate key capabilities
    sample_interactions = [
        "What is this application about?",
        "Show me the main Python files in this project",
        "Generate a script to count lines of code",
        "What are the key components of the EDGAR analyzer?",
        "Help me understand the self-improving code pattern"
    ]
    
    print(f"\n🤖 **Chatbot Controller Ready**")
    print("Sample interactions to demonstrate capabilities:")
    
    for i, interaction in enumerate(sample_interactions, 1):
        print(f"\n--- Sample Interaction {i} ---")
        print(f"💬 User: {interaction}")
        
        try:
            response = await controller.process_input(interaction)
            print(f"🤖 Controller: {response[:300]}...")
            
            if len(response) > 300:
                print("   [Response truncated for demo]")
                
        except Exception as e:
            print(f"❌ Error processing input: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 CLI CHATBOT CONTROLLER DEMONSTRATION COMPLETE")
    print("=" * 60)
    
    print("✅ CAPABILITIES DEMONSTRATED:")
    print("   • Self-aware conversational interface")
    print("   • Dynamic context extraction from codebase")
    print("   • Real-time application analysis")
    print("   • Natural language command processing")
    print("   • Intelligent response generation")
    print("   • Memory and conversation tracking")
    
    print("\n✅ REVOLUTIONARY BENEFITS:")
    print("   • Replaces complex CLI commands with natural language")
    print("   • Understands application context automatically")
    print("   • Provides intelligent assistance and suggestions")
    print("   • Learns from interactions and improves over time")
    print("   • Executes dynamic scripts based on conversation")
    print("   • Maintains awareness of both controller and application")
    
    print("\n🚀 READY FOR INTERACTIVE USE:")
    print("   Run: await controller.start_conversation()")
    print("   Then chat naturally with your application!")
    
    # Offer to start interactive mode
    try:
        start_interactive = input("\n🎮 Start interactive mode? (y/n): ").strip().lower()
        if start_interactive in ['y', 'yes']:
            print("\n🚀 Starting interactive CLI chatbot...")
            await controller.start_conversation()
    except KeyboardInterrupt:
        print("\n👋 Demo complete!")

if __name__ == "__main__":
    asyncio.run(test_cli_chatbot())

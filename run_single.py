#!/usr/bin/env python3
"""
Single Contract Review Script
Reads a specific PDF and prints the review report to stdout.
Designed to be called by the Streamlit UI.
"""

import asyncio
import sys
import argparse
from pathlib import Path
from src.tools.pdf_parser import DocumentParser
from src.agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

async def process_contract(contract_path: Path):
    """Process a single contract PDF and generate review report."""
    
    # 2. Run the workflow
    print("🤖 Agents are analyzing the contract...", flush=True)
    
    # Extract text first to print it for the UI
    # We do this manually here just to expose it to the UI, 
    # though the Intake Agent will also do it.
    # Extract text first to print it for the UI
    parser = DocumentParser()
    try:
        parsed = parser.parse(str(contract_path))
        contract_text = parsed['text']
        print(f"✓ PDF Parsed: {parsed['metadata']['pages']} pages found.")
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return

    # Print contract text for UI to capture
    print("\n---CONTRACT_TEXT_START---")
    print(contract_text)
    print("---CONTRACT_TEXT_END---\n", flush=True)
    
    # Create the prompt
    prompt = f"""Please review this contract and provide a comprehensive analysis:

CONTRACT: {parsed['metadata']['filename']}
PAGES: {parsed['metadata']['pages']}

TEXT:
{contract_text}

Provide a detailed contract review report."""
    
    print("🤖 Agents are analyzing the contract...")
    
    # Initialize runner
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="contract_review_system"
    )
    
    try:
        # Create session
        session_id = f"session_{contract_path.stem}"
        session = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id="streamlit_user",
            session_id=session_id
        )
        if not session:
            session = await runner.session_service.create_session(
                app_name=runner.app_name,
                user_id="streamlit_user",
                session_id=session_id
            )
            
        # Use run_debug which is proven to work
        # It prints to stdout, which we capture in app.py
        
        # Add a delimiter so app.py knows when the real report starts
        print("\n---REPORT_START---\n", flush=True)
        
        await runner.run_debug(
            user_messages=prompt,
            user_id="streamlit_user",
            session_id=session_id
        )
                        
        await runner.close()

    except Exception as e:
        print(f"\nAgent Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()
    
    asyncio.run(process_contract(Path(args.pdf_path)))

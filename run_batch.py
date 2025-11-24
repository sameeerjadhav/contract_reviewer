#!/usr/bin/env python3
"""
Simple Contract Review Script
Reads PDF, extracts text, and feeds it to the ADK agent using InMemoryRunner.run_debug
"""

import asyncio
import os
from pathlib import Path
from src.tools.pdf_parser import DocumentParser
from src.agent import root_agent
from google.adk.runners import InMemoryRunner

async def process_contract(contract_path: Path, runner: InMemoryRunner):
    """Process a single contract PDF and generate review report."""
    
    print(f"\n{'='*80}")
    print(f"Processing: {contract_path.name}")
    print(f"{'='*80}\n")
    
    # Parse PDF
    parser = DocumentParser()
    try:
        parsed = parser.parse(str(contract_path))
        contract_text = parsed['text']
        print(f"✓ Parsed PDF: {parsed['metadata']['pages']} pages\n")
    except Exception as e:
        print(f"✗ Error parsing PDF: {e}\n")
        return
    
    # Create the prompt
    prompt = f"""Please review this contract and provide a comprehensive analysis:

CONTRACT: {parsed['metadata']['filename']}
PAGES: {parsed['metadata']['pages']}

TEXT:
{contract_text}

Provide a detailed contract review report."""
    
    print("🤖 Running ADK Multi-Agent Review...\n")
    
    try:
        # run_debug prints events to stdout by default (quiet=False)
        # It handles session creation and message formatting
        await runner.run_debug(
            user_messages=prompt,
            user_id="batch_user",
            session_id=f"session_{contract_path.stem}"
        )
        
    except Exception as e:
        print(f"\n✗ Error during agent processing: {e}")
        import traceback
        traceback.print_exc()

async def main():
    input_dir = Path("input_contracts")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("\n⚠️  No PDF files found in input_contracts/")
        print("Place your contract PDFs there and run again.\n")
        return
    
    # Initialize runner once
    # We must provide app_name and agent as per previous error
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="contract_review_system"
    )
    
    for pdf_file in pdf_files:
        await process_contract(pdf_file, runner)
        print(f"\n{'='*80}\n")
        
    # Close runner to clean up resources
    await runner.close()

if __name__ == "__main__":
    asyncio.run(main())

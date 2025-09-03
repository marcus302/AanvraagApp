#!/usr/bin/env python3
"""
Test script for the RVO workflow
"""
import asyncio
import logging
from aanvraagapp.provider_workflows import run_rvo_workflow

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    print("Testing RVO workflow...")
    await run_rvo_workflow()


if __name__ == "__main__":
    asyncio.run(main()) 
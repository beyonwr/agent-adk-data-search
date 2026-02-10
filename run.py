#!/usr/bin/env python3
"""
Entry point for Agent ADK Data Search application.
This script runs the agent in production mode.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)


def validate_environment():
    """Validate required environment variables."""
    required_vars = [
        'PADO_API_KEY',
        'PADO_MODEL_NAME',
        'PADO_MODEL_API',
        'POSTGRESQL_DB_USER',
        'POSTGRESQL_DB_PASS',
        'POSTGRESQL_DB_NAME',
        'POSTGRESQL_DB_HOST',
        'POSTGRESQL_DB_PORT',
        'CHROMADB_HOST',
        'CHROMADB_PORT',
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file or environment configuration.")
        sys.exit(1)

    logger.info("Environment validation passed.")


async def run_agent():
    """Run the root agent."""
    try:
        # Import agent after environment validation
        from agents.agent import root_agent

        logger.info("Starting Agent ADK Data Search...")
        logger.info(f"Model: {os.getenv('ROOT_AGENT_MODEL')}")
        logger.info(f"API Base: {os.getenv('ROOT_AGENT_API_BASE')}")

        # Note: Google ADK agents typically run through specific interfaces
        # This is a placeholder for your actual execution logic
        # You might need to:
        # 1. Start an API server (FastAPI, Flask)
        # 2. Run as MCP server
        # 3. Process messages from a queue
        # 4. Or implement your custom execution loop

        logger.info("Agent initialized successfully.")
        logger.info("Root agent is ready to process requests.")

        # Keep the process alive
        # Replace this with your actual agent execution logic
        while True:
            await asyncio.sleep(60)
            logger.info("Agent is running...")

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Agent ADK Data Search - Production Mode")
    logger.info("=" * 60)

    # Validate environment
    validate_environment()

    # Create artifacts directory
    artifacts_dir = Path('/app/artifacts/agents')
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Artifacts directory: {artifacts_dir}")

    # Run the agent
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()

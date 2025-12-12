"""
Entry point for the parking entry monitoring service.
"""
import logging
import argparse
import sys

from config import Config
from pipelines.entry_pipeline import EntryPipeline


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('entry_pipeline.log')
        ]
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Parking Entry Monitoring Service')
    parser.add_argument('--camera', type=str, default=None,
                       help='Camera source (URL or device index)')
    parser.add_argument('--no-display', action='store_true',
                       help='Disable video display')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Parking Entry Monitoring Service")
    
    try:
        # Load and validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize pipeline
        pipeline = EntryPipeline(Config)
        
        # Run pipeline
        pipeline.run(
            camera_source=args.camera,
            display=not args.no_display
        )
        
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

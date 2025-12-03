"""
Logging utility module for rotating daily log files and cleaning old logs.
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path


class DailyRotatingFileHandler(logging.FileHandler):
    """Custom logging handler that rotates log files daily"""
    
    def __init__(self, log_dir='logs'):
        """Initialize the handler
        
        Args:
            log_dir: Directory to store log files (default: 'logs')
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Set initial filename
        self.base_filename = 'alarm_service'
        self.log_filename = self._get_log_filename()
        
        super().__init__(str(self.log_filename))
        self.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
    
    def _get_log_filename(self):
        """Generate log filename with current date
        
        Returns:
            Path: Full path to log file (e.g., logs/2025-12-03_alarm_service.log)
        """
        today = datetime.now().strftime('%Y-%m-%d')
        return self.log_dir / f"{today}_{self.base_filename}.log"
    
    def emit(self, record):
        """Override emit to check for date change and rotate if needed"""
        current_log_filename = self._get_log_filename()
        
        # If date has changed, close old handler and open new one
        if str(current_log_filename) != self.baseFilename:
            self.close()
            self.baseFilename = str(current_log_filename)
            if self.stream:
                self.stream.close()
                self.stream = None
            self.stream = self._open()
            self.clean_old_logs()
        
        super().emit(record)
    
    def clean_old_logs(self, days=30):
        """Remove log files older than specified days
        
        Args:
            days: Number of days to keep (default: 30)
        """
        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=days)
            
            for log_file in self.log_dir.glob('*_alarm_service.log'):
                # Extract date from filename (format: YYYY-MM-DD_alarm_service.log)
                try:
                    date_str = log_file.name.split('_')[0]
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        print(f"Deleted old log file: {log_file.name}")
                except (ValueError, IndexError):
                    # Skip files that don't match the expected format
                    pass
        except Exception as e:
            print(f"Error cleaning old logs: {e}")


def setup_logger(name, log_dir='logs', level=logging.INFO):
    """Setup logger with daily rotating file handler
    
    Args:
        name: Logger name
        log_dir: Directory to store log files (default: 'logs')
        level: Logging level (default: logging.INFO)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add file handler with daily rotation
    file_handler = DailyRotatingFileHandler(log_dir)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)
    
    return logger

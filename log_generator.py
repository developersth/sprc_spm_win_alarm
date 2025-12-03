import logging


class LogNumberGenerator:
    """Generates unique sequential log numbers"""
    
    def __init__(self):
        """Initialize log number generator"""
        self.log_counter = 0
        self.last_date = None
    
    def generate(self):
        """Generate unique sequential log number
        
        Format: YYMMDDHH (8 digits) + 4-digit counter
        Example: 25120100 (YY=25, MM=12, DD=01, HH=00) + 0001 = 251201000001
        
        Returns:
            str: Unique log number
        """
        from datetime import datetime
        
        current_time = datetime.now().strftime('%y%m%d%H')
        
        # Reset counter if hour changes
        if current_time != self.last_date:
            self.log_counter = 0
            self.last_date = current_time
        
        # Increment counter
        self.log_counter += 1
        
        # Generate log number with format: YYMMDDHH + counter (4 digits)
        log_no = f"{current_time}{self.log_counter:04d}"
        
        return log_no

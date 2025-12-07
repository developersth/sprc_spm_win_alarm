import logging
import psycopg2
from datetime import datetime
import time

class DatabaseManager:
    """Manages all database operations for the alarm system"""
    
    def __init__(self, config):
        """Initialize database manager with configuration"""
        self.config = config
        self.connection = None
        self.log_counter = 0
        self.last_date = None
        self.connect()
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            db_config = self.config['database']
            self.connection = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            logging.info("Database connected successfully")
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            raise
    
    def is_connected(self):
        """Check if database is connected"""
        return self.connection is not None and not self.connection.closed
    
    def load_alarm_mapping(self):
        """Load alarm mapping configuration from database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT item, description, signal_type, close_status, 
                       alarm_status, priority, address, bit_no, 
                       modbus_function, enabled
                FROM alarm_mapping
                WHERE enabled = TRUE
                ORDER BY item
            """)
            
            mappings = []
            for row in cursor.fetchall():
                mapping = {
                    'item': row[0],
                    'description': row[1],
                    'signal_type': row[2],
                    'close_status': row[3],
                    'alarm_status': row[4],
                    'priority': row[5],
                    'address': int(row[6]),
                    'bit_no': row[7],
                    'modbus_function': row[8],
                    'enabled': row[9]
                }
                mappings.append(mapping)
            
            cursor.close()
            logging.info(f"Loaded {len(mappings)} alarm mappings from database")
            return mappings
            
        except Exception as e:
            logging.error(f"Error loading alarm mapping: {e}")
            return []
    
    def generate_log_number(self):
        """Generate unique sequential log number
        
        Format: YYMMDDHH (8 digits) + 4-digit counter
        Example: 25120100 (YY=25, MM=12, DD=01, HH=00) + 0001 = 251201000001
        """
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
    
    def save_alarm(self, alarm_info, machine_name):
        """Save alarm event to database"""
        try:
            cursor = self.connection.cursor()
            
            log_no = self.generate_log_number()
            
            cursor.execute("""
                INSERT INTO alarm_history 
                (log_no, date_time, type, description, status, machine)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                log_no,
                datetime.now(),
                alarm_info['type'],
                alarm_info['description'],
                alarm_info['status'],
                machine_name
            ))
            
            self.connection.commit()
            cursor.close()
            
            logging.info(f"Alarm saved: {alarm_info['description']} - {alarm_info['status']}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving alarm to database: {e}")
            self.connection.rollback()
            return False
    
    def get_alarm_history(self, filters=None, limit=1000):
        """Get alarm history with optional filters
        
        Args:
            filters: Dictionary with optional filters
                - start_date: datetime
                - end_date: datetime
                - alarm_type: str (Alarm/Event)
                - status: str
                - machine: str
                - description: str
                - search_text: str (for partial matches)
            limit: Maximum number of records to return
        
        Returns:
            List of alarm records
        """
        try:
            cursor = self.connection.cursor()
            
            query = "SELECT log_no, date_time, type, description, status, machine FROM alarm_history WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('start_date'):
                    query += " AND date_time >= %s"
                    params.append(filters['start_date'])
                
                if filters.get('end_date'):
                    query += " AND date_time <= %s"
                    params.append(filters['end_date'])
                
                if filters.get('alarm_type') and filters['alarm_type'] != 'All':
                    query += " AND type = %s"
                    params.append(filters['alarm_type'])
                
                if filters.get('status') and filters['status'] != 'All':
                    query += " AND LOWER(COALESCE(status, '')) = LOWER(%s)"
                    params.append(filters['status'])
                
                if filters.get('machine') and filters['machine'] != 'All':
                    query += " AND machine = %s"
                    params.append(filters['machine'])
                
                if filters.get('description') and filters['description'] != 'All':
                    query += " AND description = %s"
                    params.append(filters['description'])
                
                if filters.get('search_text'):
                    query += " AND (description ILIKE %s OR log_no ILIKE %s OR status ILIKE %s)"
                    search = f"%{filters['search_text']}%"
                    params.append(search)
                    params.append(search)
                    params.append(search)
            
            query += f" ORDER BY date_time DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            records = cursor.fetchall()
            cursor.close()
            
            return records
            
        except Exception as e:
            logging.error(f"Error retrieving alarm history: {e}")
            return []
    
    def get_distinct_descriptions(self):
        """Get list of distinct descriptions for filter dropdown"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT DISTINCT description FROM alarm_history ORDER BY description")
            descriptions = ['All'] + [row[0] for row in cursor.fetchall()]
            cursor.close()
            return descriptions
        except Exception as e:
            logging.error(f"Error retrieving descriptions: {e}")
            return ['All']
    
    def get_distinct_statuses(self):
        """Get list of distinct statuses for filter dropdown"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT DISTINCT COALESCE(status, 'Unknown') FROM alarm_history WHERE status IS NOT NULL ORDER BY status")
            statuses = ['All'] + [row[0] for row in cursor.fetchall() if row[0]]
            cursor.close()
            # Remove duplicates while preserving order
            seen = set()
            unique_statuses = []
            for s in statuses:
                if s not in seen:
                    seen.add(s)
                    unique_statuses.append(s)
            return unique_statuses
        except Exception as e:
            logging.error(f"Error retrieving statuses: {e}")
            return ['All']
    
    def get_distinct_machines(self):
        """Get list of distinct machines for filter dropdown"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT DISTINCT machine FROM alarm_history ORDER BY machine")
            machines = ['All'] + [row[0] for row in cursor.fetchall() if row[0]]
            cursor.close()
            return machines
        except Exception as e:
            logging.error(f"Error retrieving machines: {e}")
            return ['All']
    
    def get_record_count(self, filters=None):
        """Get total count of alarm records with optional filters"""
        try:
            cursor = self.connection.cursor()
            
            query = "SELECT COUNT(*) FROM alarm_history WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('start_date'):
                    query += " AND date_time >= %s"
                    params.append(filters['start_date'])
                
                if filters.get('end_date'):
                    query += " AND date_time <= %s"
                    params.append(filters['end_date'])
            
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            cursor.close()
            
            return count
        except Exception as e:
            logging.error(f"Error getting record count: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logging.info("Database connection closed")

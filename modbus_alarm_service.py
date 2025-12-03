import time
import logging
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import threading
import json
from database import DatabaseManager
from log_manager import setup_logger

# Configure logging with daily rotation
logger = setup_logger('alarm_service', log_dir='logs')

class ModbusAlarmMonitor:
    def __init__(self, config_file='app_config.json'):
        """Initialize Modbus Alarm Monitor"""
        self.config = self.load_config(config_file)
        self.modbus_client = None
        self.db_manager = None
        self.alarm_states = {}  # Track previous alarm states
        self.running = False
        self.monitor_thread = None
        
        # Initialize database manager
        self.db_manager = DatabaseManager(self.config)
        
        # Load alarm mapping from database
        self.alarm_mapping = self.db_manager.load_alarm_mapping()
        
        logger.info("Modbus Alarm Monitor initialized")
    
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found. Using default configuration.")
            return {
                "modbus": {
                    "mode": "real",
                    "hosts": {
                        "sim": {
                            "host": "localhost",
                            "port": 1502
                        },
                        "real": {
                            "host": "192.168.1.100",
                            "port": 502
                        }
                    },
                    "timeout": 3,
                    "reconnect_delay": 0.1,
                    "reconnect_delay_max": 300,
                    "retries": 3
                },
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "alarm_history",
                    "user": "admin",
                    "password": "admin123"
                },
                "monitoring": {
                    "scan_interval": 1.0,
                    "machine_name": "Mastercomm"
                }
            }
    
    def connect_modbus(self):
        """Connect to Modbus TCP server"""
        try:
            modbus_config = self.config['modbus']
            
            # Get mode and select host configuration
            mode = modbus_config.get('mode', 'real')
            host_config = modbus_config['hosts'][mode]
            
            logger.info(f"Connecting to Modbus in {mode.upper()} mode")
            
            self.modbus_client = ModbusTcpClient(
                host=host_config['host'],
                port=host_config['port'],
                timeout=modbus_config['timeout'],
                retries=modbus_config['retries']
            )
            
            if self.modbus_client.connect():
                logger.info(f"Modbus connected to {host_config['host']}:{host_config['port']} ({mode.upper()} mode)")
                return True
            else:
                logger.error("Failed to connect to Modbus server")
                return False
                
        except Exception as e:
            logger.error(f"Modbus connection error: {e}")
            return False
    
    def read_coil(self, address, count=1):
        """Read coil status from Modbus (Function Code 01)"""
        try:
            response = self.modbus_client.read_coils(address, count=count)
            if not response.isError():
                return response.bits[:count]
            else:
                logger.error(f"Error reading coil at address {address}")
                return None
        except ModbusException as e:
            logger.error(f"Modbus exception reading coil {address}: {e}")
            return None
    
    def read_discrete_input(self, address, count=1):
        """Read discrete input from Modbus (Function Code 02)"""
        try:
            response = self.modbus_client.read_discrete_inputs(address, count=count)
            if not response.isError():
                return response.bits[:count]
            else:
                logger.error(f"Error reading discrete input at address {address}")
                return None
        except ModbusException as e:
            logger.error(f"Modbus exception reading discrete input {address}: {e}")
            return None
    
    def save_alarm_to_database(self, alarm_info):
        """Save alarm event to database"""
        self.db_manager.save_alarm(alarm_info, self.config['monitoring']['machine_name'])
    
    def process_alarm(self, mapping, current_state):
        """Process alarm state change"""
        item = mapping['item']
        previous_state = self.alarm_states.get(item, False)
        
        # Detect state change
        if current_state != previous_state:
            alarm_info = {
                'type': 'Alarm' if current_state else 'Event',
                'description': mapping['description'],
                'status': mapping['close_status'] if current_state else 'Normal',
                'priority': mapping['priority']
            }
            
            # Save to database
            self.save_alarm_to_database(alarm_info)
            
            # Update state
            self.alarm_states[item] = current_state
            
            # Log state change
            state_text = "ACTIVE" if current_state else "CLEARED"
            logger.info(f"Alarm {item}: {mapping['description']} - {state_text}")
    
    def scan_alarms(self):
        """Scan all configured alarms"""
        if not self.modbus_client or not self.modbus_client.is_socket_open():
            logger.warning("Modbus not connected. Attempting reconnection...")
            if not self.connect_modbus():
                return
        
        for mapping in self.alarm_mapping:
            try:
                address = mapping['address']
                
                # Read based on Modbus function
                if '01' in mapping['modbus_function']:  # Read Coils
                    result = self.read_coil(address)
                elif '02' in mapping['modbus_function']:  # Read Discrete Inputs
                    result = self.read_discrete_input(address)
                else:
                    logger.warning(f"Unsupported Modbus function for {mapping['description']}")
                    continue
                
                if result is not None and len(result) > 0:
                    current_state = result[0]
                    self.process_alarm(mapping, current_state)
                    
            except Exception as e:
                logger.error(f"Error scanning alarm {mapping['description']}: {e}")
    
    def monitoring_loop(self):
        """Main monitoring loop"""
        scan_interval = self.config['monitoring']['scan_interval']
        
        logger.info("Monitoring started")
        
        while self.running:
            try:
                self.scan_alarms()
                time.sleep(scan_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retry
    
    def start(self):
        """Start alarm monitoring"""
        if self.running:
            logger.warning("Monitor is already running")
            return
        
        # Connect to Modbus
        if not self.connect_modbus():
            logger.error("Cannot start monitoring - Modbus connection failed")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Alarm monitoring started")
    
    def stop(self):
        """Stop alarm monitoring"""
        if not self.running:
            logger.warning("Monitor is not running")
            return
        
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.modbus_client:
            self.modbus_client.close()
        
        logger.info("Alarm monitoring stopped")
    
    def get_status(self):
        """Get current monitoring status"""
        status = {
            'running': self.running,
            'modbus_connected': self.modbus_client.is_socket_open() if self.modbus_client else False,
            'database_connected': self.db_manager.is_connected(),
            'active_alarms': sum(1 for state in self.alarm_states.values() if state),
            'total_monitored': len(self.alarm_mapping)
        }
        return status
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop()
        
        if self.db_manager:
            self.db_manager.close()

def main():
    """Main function for standalone execution"""
    print("=" * 60)
    print("Modbus Alarm Monitoring Service")
    print("=" * 60)
    
    monitor = ModbusAlarmMonitor()
    
    try:
        monitor.start()
        
        print("\nMonitoring started. Press Ctrl+C to stop.\n")
        
        # Status update loop
        while True:
            time.sleep(30)
            status = monitor.get_status()
            print(f"\nStatus: Running={status['running']}, "
                  f"Modbus={status['modbus_connected']}, "
                  f"DB={status['database_connected']}, "
                  f"Active Alarms={status['active_alarms']}/{status['total_monitored']}")
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        monitor.stop()
        print("Service stopped.")

if __name__ == "__main__":
    main()
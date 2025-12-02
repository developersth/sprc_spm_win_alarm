# โค้ดที่เรียบง่ายสำหรับ pymodbus 3.11.4
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification

import threading
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModbusSimulator:
    def __init__(self, host='0.0.0.0', port=1502):
        self.host = host
        self.port = port
        self.simulator_thread = None
        self.running = False

        # สร้าง datastore
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0]*1000),
            co=ModbusSequentialDataBlock(0, [0]*1000),
            hr=ModbusSequentialDataBlock(0, [0]*1000),
            ir=ModbusSequentialDataBlock(0, [0]*1000),
            zero_mode=True
        )
        self.context = ModbusServerContext(slaves=store, single=True)
        
        # เก็บ reference ถึง coils สำหรับการจำลอง
        self.coils = store.getStore('c')

        # Device identification
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = 'PyModbus Simulator'
        self.identity.ProductCode = 'ALARM-SIM'
        self.identity.ProductName = 'Alarm System Simulator'
        self.identity.MajorMinorRevision = '1.0.0'

    def start(self):
        if self.running:
            logger.warning("Simulator already running")
            return

        self.running = True
        
        # สร้าง thread สำหรับการจำลอง
        self.simulator_thread = threading.Thread(target=self._simulate_alarms, daemon=True)
        self.simulator_thread.start()
        
        logger.info(f"Starting Modbus server at {self.host}:{self.port}")
        
        # รัน server ใน thread หลัก (blocking)
        try:
            StartTcpServer(
                context=self.context,
                identity=self.identity,
                address=(self.host, self.port)
            )
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False

    def _simulate_alarms(self):
        # แอดเดรสแบบ 0-based สำหรับ internal storage
        alarm_addresses = [1, 3, 16, 17, 18, 19, 20, 48, 49, 50, 51, 52]
        
        while self.running:
            try:
                # 15% โอกาสที่จะเปลี่ยนสถานะ alarm
                if random.random() < 0.15:
                    addr = random.choice(alarm_addresses)
                    
                    # อ่านค่าปัจจุบัน
                    current_value = self.coils.getValues(addr, 1)[0]
                    
                    # สลับค่า (0->1, 1->0)
                    new_value = 1 if current_value == 0 else 0
                    
                    # ตั้งค่าใหม่
                    self.coils.setValues(addr, [new_value])
                    
                    # Log ด้วยแอดเดรส Modbus ที่ถูกต้อง (+1)
                    modbus_addr = addr + 1
                    status = "ACTIVE" if new_value == 1 else "CLEARED"
                    logger.info(f"Alarm at Modbus address {modbus_addr}: {status}")
                
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                time.sleep(5)

    def stop(self):
        self.running = False
        if self.simulator_thread and self.simulator_thread.is_alive():
            self.simulator_thread.join(timeout=2)
        logger.info("Simulator stopped")

if __name__ == "__main__":
    sim = ModbusSimulator()
    try:
        print("=" * 60)
        print("Modbus Alarm Simulator")
        print(f"Listening on: 0.0.0.0:1502")
        print("Simulating alarms at addresses: 2, 4, 17, 18, 19, 20, 21, 49, 50, 51, 52, 53")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        # เริ่ม simulator ใน thread แยก
        import threading
        sim_thread = threading.Thread(target=sim.start, daemon=True)
        sim_thread.start()
        
        # รอจนกว่าจะถูก interrupt
        while sim.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        sim.stop()
    except Exception as e:
        print(f"Error: {e}")
        sim.stop()
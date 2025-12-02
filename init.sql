-- Create alarm history table
CREATE TABLE IF NOT EXISTS alarm_history (
    id SERIAL PRIMARY KEY,
    log_no VARCHAR(50) NOT NULL,
    date_time TIMESTAMP NOT NULL,
    type VARCHAR(20) NOT NULL,
    description VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    machine VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create alarm mapping table
CREATE TABLE IF NOT EXISTS alarm_mapping (
    id SERIAL PRIMARY KEY,
    item INTEGER NOT NULL,
    description VARCHAR(255) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,
    open_status VARCHAR(20),
    close_status VARCHAR(20),
    enabled VARCHAR(20),
    alarm_status VARCHAR(20),
    priority VARCHAR(20),
    address VARCHAR(10),
    bit_no INTEGER,
    rw VARCHAR(5),
    modbus_data_type VARCHAR(20),
    modbus_function VARCHAR(50),
    comments TEXT
);

-- Create indexes for better performance
CREATE INDEX idx_alarm_history_datetime ON alarm_history(date_time DESC);
CREATE INDEX idx_alarm_history_type ON alarm_history(type);
CREATE INDEX idx_alarm_history_status ON alarm_history(status);
CREATE INDEX idx_alarm_history_machine ON alarm_history(machine);
CREATE INDEX idx_alarm_history_log_no ON alarm_history(log_no);

-- Insert sample alarm mapping data
INSERT INTO alarm_mapping (item, description, signal_type, open_status, close_status, enabled, alarm_status, priority, address, bit_no, rw, modbus_data_type, modbus_function, comments) VALUES
(1, 'Mastercomm Restart', 'Boolean', 'NORMAL', 'RESTART', 'ENABLE', 'CLOSE', 'HIGH', '0002', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(2, 'Mastercomm GPS Fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0004', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(3, 'SPM BUOY Power/Communications Fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0017', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(4, 'SPM BUOY WA Restart flag', 'Boolean', 'NORMAL', 'RESTART', 'ENABLE', 'CLOSE', 'HIGH', '0018', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(5, 'SPM BUOY GPS Fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0019', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(6, 'SPM BUOY Sensor A fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0020', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(7, 'SPM BUOY Sensor B fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0021', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(8, 'RECEIVING TERMINALS Power/Communications Fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0049', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(9, 'RECEIVING TERMINALS WA Restart flag', 'Boolean', 'NORMAL', 'RESTART', 'ENABLE', 'CLOSE', 'HIGH', '0050', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(10, 'RECEIVING TERMINALS GPS Fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0051', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(11, 'RECEIVING TERMINALS Sensor A fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0052', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL),
(12, 'RECEIVING TERMINALS Sensor B fault', 'Boolean', 'NORMAL', 'FAULT', 'ENABLE', 'CLOSE', 'HIGH', '0053', 0, 'R', 'Coil', '01: READ OUTPUT STATUS', NULL);

-- Insert sample alarm history data
INSERT INTO alarm_history (log_no, date_time, type, description, status, machine) VALUES
('8293150104', '2025-01-12 07:06:58', 'Alarm', 'Mastercomm Restart', 'Restart', 'Mastercomm'),
('8293150103', '2025-10-28 08:06:50', 'Alarm', 'Mastercomm GPS Fault', 'Fault', 'Mastercomm'),
('8293150102', '2025-10-28 10:06:54', 'Event', 'SPM BUOY Power', 'Normal', 'Mastercomm'),
('8293150101', '2025-10-28 16:07:53', 'Alarm', 'SPM BUOY WA Restart flag', 'Restart', 'Mastercomm'),
('8293132381', '2025-10-27 08:16:27', 'Alarm', 'SPM BUOY GPS Fault', 'Fault', 'Mastercomm'),
('8293132380', '2025-10-27 10:17:28', 'Alarm', 'SPM BUOY Sensor A fault', 'Fault', 'Mastercomm'),
('8293132379', '2025-10-27 11:19:25', 'Alarm', 'SPM BUOY Sensor B fault', 'Fault', 'Mastercomm'),
('8293132378', '2025-10-27 13:16:28', 'Event', 'RECEIVING TERMINALS Power', 'Normal', 'Mastercomm'),
('8293132377', '2025-10-27 17:19:23', 'Alarm', 'RECEIVING TERMINALS WA', 'Clear', 'Mastercomm'),
('8293132376', '2025-10-27 18:16:21', 'Alarm', 'RECEIVING TERMINALS GPS', 'Test', 'Mastercomm');
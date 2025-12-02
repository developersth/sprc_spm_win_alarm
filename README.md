python3 -m venv venv

✅ 3) เปิดใช้งาน Environment
Windows (PowerShell)
.\venv\Scripts\activate

Windows (CMD)
venv\Scripts\activate.bat

macOS / Linux
source venv/bin/activate

pip freeze > requirements.txt

python3 -m venv venv
source venv/bin/activate    # (Windows: venv\Scripts\activate)
pip install -r requirements.txt

python3 -m pip install --upgrade pip

# Alarm History Log System

ระบบบันทึกและแสดงประวัติ Alarm สำหรับ Mastercomm โดยใช้ Python GUI (tkinter) และ PostgreSQL Database

## คุณสมบัติ

- 🔍 ค้นหาและกรองข้อมูล Alarm ตามวันที่, เวลา, ประเภท, รายละเอียด และสถานะ
- 📊 แสดงข้อมูลในรูปแบบตารางพร้อมสีแยกตามประเภท Alarm
- 💾 ส่งออกข้อมูลเป็นไฟล์ CSV
- 🔄 Refresh ข้อมูลแบบ Real-time
- 🗄️ เก็บข้อมูลใน PostgreSQL Database พร้อม Docker support

## โครงสร้างไฟล์

```
alarm-history-system/
├── docker-compose.yml      # Docker configuration สำหรับ PostgreSQL
├── init.sql               # SQL script สำหรับสร้างตารางและข้อมูลเริ่มต้น
├── alarm_history_app.py   # Python GUI application
├── requirements.txt       # Python dependencies
└── README.md             # คู่มือการใช้งาน
```

## การติดตั้ง

### 1. ติดตั้ง Docker และ Docker Compose

สำหรับ Windows:
- ดาวน์โหลดและติดตั้ง [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 2. Clone หรือสร้างโปรเจค

สร้างโฟลเดอร์และวางไฟล์ทั้งหมดลงไปในโฟลเดอร์เดียวกัน

### 3. เริ่มต้น PostgreSQL Database

เปิด Command Prompt หรือ PowerShell ในโฟลเดอร์โปรเจค และรันคำสั่ง:

```bash
docker-compose up -d
```

คำสั่งนี้จะ:
- ดาวน์โหลด PostgreSQL image
- สร้าง database ชื่อ `alarm_history`
- รันไฟล์ `init.sql` เพื่อสร้างตารางและข้อมูลตัวอย่าง
- เริ่มต้น pgAdmin (web-based database management)

ตรวจสอบสถานะ:
```bash
docker-compose ps
```

### 4. ติดตั้ง Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. รัน Application

```bash
python alarm_history_app.py
```

## ข้อมูล Database Connection

**PostgreSQL:**
- Host: `localhost`
- Port: `5432`
- Database: `alarm_history`
- Username: `admin`
- Password: `admin123`

**pgAdmin (Web Interface):**
- URL: http://localhost:5050
- Email: `admin@admin.com`
- Password: `admin123`

## การใช้งาน

### ค้นหาและกรองข้อมูล

1. **เลือกช่วงวันที่**: ใช้ Date Picker เลือก From Date และ To Date
2. **กรองตามประเภท**: เลือก Alarm หรือ Event
3. **กรองตามรายละเอียด**: เลือกจาก dropdown list
4. **กรองตามสถานะ**: เลือก Normal, Fault, Restart, Clear หรือ Test
5. **ค้นหาข้อความ**: พิมพ์คำค้นหาในช่อง Search
6. **คลิกปุ่ม Search**: เพื่อแสดงผลลัพธ์

### ส่งออกข้อมูล

1. คลิกปุ่ม **Export CSV**
2. เลือกตำแหน่งที่จะบันทึกไฟล์
3. ตั้งชื่อไฟล์และคลิก Save

### Refresh ข้อมูล

คลิกปุ่ม **Refresh** เพื่ออัพเดตข้อมูลล่าสุดจาก Database

## โครงสร้าง Database

### ตาราง alarm_history

| Column      | Type         | Description                    |
|-------------|--------------|--------------------------------|
| id          | SERIAL       | Primary key                    |
| log_no      | VARCHAR(50)  | เลขที่ Log                     |
| date_time   | TIMESTAMP    | วันที่และเวลาที่เกิด Alarm      |
| type        | VARCHAR(20)  | ประเภท (Alarm/Event)           |
| description | VARCHAR(255) | รายละเอียด Alarm               |
| status      | VARCHAR(20)  | สถานะ (Normal/Fault/Restart)  |
| machine     | VARCHAR(100) | ชื่อเครื่อง                    |
| created_at  | TIMESTAMP    | วันที่บันทึกข้อมูล             |

### ตาราง alarm_mapping

เก็บข้อมูล mapping ระหว่าง alarm กับ Modbus address และ configuration ต่างๆ

## การเพิ่มข้อมูล Alarm ใหม่

### ผ่าน SQL

```sql
INSERT INTO alarm_history (log_no, date_time, type, description, status, machine) 
VALUES ('8293150105', NOW(), 'Alarm', 'Test Alarm', 'Normal', 'Mastercomm');
```

### ผ่าน Python

```python
import psycopg2

conn = psycopg2.connect(
    user="admin",
    password="admin123",
    host="localhost",
    port="5432",
    database="alarm_history"
)

cursor = conn.cursor()
cursor.execute("""
    INSERT INTO alarm_history (log_no, date_time, type, description, status, machine) 
    VALUES (%s, NOW(), %s, %s, %s, %s)
""", ('8293150105', 'Alarm', 'Test Alarm', 'Normal', 'Mastercomm'))
conn.commit()
cursor.close()
conn.close()
```

## คำสั่ง Docker ที่เป็นประโยชน์

```bash
# เริ่มต้น containers
docker-compose up -d

# หยุด containers
docker-compose stop

# ลบ containers (ข้อมูลจะยังอยู่)
docker-compose down

# ลบทั้ง containers และข้อมูล
docker-compose down -v

# ดู logs
docker-compose logs -f postgres

# เข้าไปใน PostgreSQL CLI
docker exec -it alarm_history_db psql -U admin -d alarm_history
```

## Troubleshooting

### ไม่สามารถเชื่อมต่อ Database

1. ตรวจสอบว่า Docker containers กำลังรันอยู่:
   ```bash
   docker-compose ps
   ```

2. ตรวจสอบ logs:
   ```bash
   docker-compose logs postgres
   ```

3. ทดสอบการเชื่อมต่อด้วย pgAdmin หรือ psql

### Port 5432 ถูกใช้งานอยู่

ถ้า Port 5432 ถูกใช้งานโดยโปรแกรมอื่น ให้แก้ไขไฟล์ `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"  # เปลี่ยนจาก 5432:5432
```

และแก้ไขใน Python code:
```python
port="5433"  # เปลี่ยนจาก 5432
```

### ปัญหา Python Libraries

ถ้าติดตั้ง `psycopg2-binary` ไม่สำเร็จ ให้ลองใช้:
```bash
pip install psycopg2-binary --no-cache-dir
```

## License

MIT License

## ผู้พัฒนา

พัฒนาโดย Claude AI - สำหรับระบบ Alarm History Logging

## run docker prosgress sql
docker compose up -d   
 docker compose down   
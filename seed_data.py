#!/usr/bin/env python3
"""
Seed script to populate the database with sample data for testing
Hardware Inventory Tracker
"""

from app import app, db
from models import HardwareType, LotNumber, Box, PullEvent
from datetime import datetime, timezone, timedelta
import random

def seed_database():
    """Populate database with realistic sample data"""
    
    with app.app_context():
        # Clear existing data
        db.session.query(PullEvent).delete()
        db.session.query(Box).delete()
        db.session.query(HardwareType).delete()
        db.session.query(LotNumber).delete()
        
        # Create hardware types
        hardware_types = [
            'Resistors_1K_Ohm',
            'Capacitors_100uF',
            'Microcontrollers_ESP32',
            'LED_Red_5mm',
            'Sensors_Temperature',
            'Connectors_USB_C',
            'Transistors_NPN',
            'IC_OpAmp_741'
        ]
        
        type_objects = []
        for type_name in hardware_types:
            ht = HardwareType(name=type_name)
            db.session.add(ht)
            type_objects.append(ht)
        
        # Create lot numbers
        lot_numbers = [
            'LOT2024-001',
            'LOT2024-002', 
            'LOT2024-003',
            'LOT2024-004',
            'LOT2024-005',
            'BATCH-A001',
            'BATCH-B002',
            'BATCH-C003'
        ]
        
        lot_objects = []
        for lot_name in lot_numbers:
            ln = LotNumber(name=lot_name)
            db.session.add(ln)
            lot_objects.append(ln)
        
        db.session.flush()  # Get IDs
        
        # Create boxes
        box_configs = [
            # Resistors
            {'type': 'Resistors_1K_Ohm', 'lot': 'LOT2024-001', 'box': '001', 'qty': 500, 'barcode': 'RES1K001A'},
            {'type': 'Resistors_1K_Ohm', 'lot': 'LOT2024-001', 'box': '002', 'qty': 500, 'barcode': 'RES1K002A'},
            {'type': 'Resistors_1K_Ohm', 'lot': 'LOT2024-002', 'box': '001', 'qty': 750, 'barcode': 'RES1K001B'},
            
            # Capacitors
            {'type': 'Capacitors_100uF', 'lot': 'LOT2024-001', 'box': '001', 'qty': 200, 'barcode': 'CAP100_001A'},
            {'type': 'Capacitors_100uF', 'lot': 'LOT2024-002', 'box': '001', 'qty': 300, 'barcode': 'CAP100_001B'},
            {'type': 'Capacitors_100uF', 'lot': 'LOT2024-002', 'box': '002', 'qty': 300, 'barcode': 'CAP100_002B'},
            
            # Microcontrollers
            {'type': 'Microcontrollers_ESP32', 'lot': 'BATCH-A001', 'box': '001', 'qty': 50, 'barcode': 'ESP32_001A'},
            {'type': 'Microcontrollers_ESP32', 'lot': 'BATCH-A001', 'box': '002', 'qty': 50, 'barcode': 'ESP32_002A'},
            {'type': 'Microcontrollers_ESP32', 'lot': 'BATCH-B002', 'box': '001', 'qty': 75, 'barcode': 'ESP32_001B'},
            
            # LEDs
            {'type': 'LED_Red_5mm', 'lot': 'LOT2024-003', 'box': '001', 'qty': 1000, 'barcode': 'LED_RED_001C'},
            {'type': 'LED_Red_5mm', 'lot': 'LOT2024-003', 'box': '002', 'qty': 1000, 'barcode': 'LED_RED_002C'},
            {'type': 'LED_Red_5mm', 'lot': 'LOT2024-004', 'box': '001', 'qty': 800, 'barcode': 'LED_RED_001D'},
            
            # Temperature Sensors
            {'type': 'Sensors_Temperature', 'lot': 'BATCH-A001', 'box': '001', 'qty': 100, 'barcode': 'TEMP_001A'},
            {'type': 'Sensors_Temperature', 'lot': 'BATCH-B002', 'box': '001', 'qty': 120, 'barcode': 'TEMP_001B'},
            
            # USB-C Connectors
            {'type': 'Connectors_USB_C', 'lot': 'LOT2024-005', 'box': '001', 'qty': 250, 'barcode': 'USB_C_001E'},
            {'type': 'Connectors_USB_C', 'lot': 'LOT2024-005', 'box': '002', 'qty': 250, 'barcode': 'USB_C_002E'},
            
            # Transistors
            {'type': 'Transistors_NPN', 'lot': 'BATCH-C003', 'box': '001', 'qty': 400, 'barcode': 'NPN_001C'},
            {'type': 'Transistors_NPN', 'lot': 'BATCH-C003', 'box': '002', 'qty': 400, 'barcode': 'NPN_002C'},
            
            # OpAmps
            {'type': 'IC_OpAmp_741', 'lot': 'LOT2024-004', 'box': '001', 'qty': 150, 'barcode': 'IC741_001D'},
            {'type': 'IC_OpAmp_741', 'lot': 'LOT2024-005', 'box': '001', 'qty': 200, 'barcode': 'IC741_001E'}
        ]
        
        boxes = []
        for config in box_configs:
            # Find type and lot objects
            hw_type = next(t for t in type_objects if t.name == config['type'])
            lot_num = next(l for l in lot_objects if l.name == config['lot'])
            
            # Generate box ID
            box_id = f"{config['type']}_{config['lot']}_{config['box']}"
            
            # Create box
            box = Box(
                box_id=box_id,
                hardware_type_id=hw_type.id,
                lot_number_id=lot_num.id,
                box_number=config['box'],
                initial_quantity=config['qty'],
                remaining_quantity=config['qty'],
                barcode=config['barcode']
            )
            db.session.add(box)
            boxes.append(box)
        
        db.session.flush()  # Get box IDs
        
        # Create some pull events to simulate real usage
        pull_events = [
            # Resistor pulls
            {'barcode': 'RES1K001A', 'qty': 50, 'qc': 'John Smith', 'sig': 'JS-001'},
            {'barcode': 'RES1K001A', 'qty': 25, 'qc': 'Jane Doe', 'sig': 'JD-002'},
            {'barcode': 'RES1K002A', 'qty': 100, 'qc': 'Mike Johnson', 'sig': 'MJ-003'},
            
            # Capacitor pulls
            {'barcode': 'CAP100_001A', 'qty': 20, 'qc': 'Sarah Wilson', 'sig': 'SW-004'},
            {'barcode': 'CAP100_001B', 'qty': 15, 'qc': 'John Smith', 'sig': 'JS-005'},
            
            # ESP32 pulls
            {'barcode': 'ESP32_001A', 'qty': 5, 'qc': 'Tech Team Lead', 'sig': 'TTL-006'},
            {'barcode': 'ESP32_002A', 'qty': 3, 'qc': 'Jane Doe', 'sig': 'JD-007'},
            
            # LED pulls
            {'barcode': 'LED_RED_001C', 'qty': 150, 'qc': 'Mike Johnson', 'sig': 'MJ-008'},
            {'barcode': 'LED_RED_002C', 'qty': 200, 'qc': 'Sarah Wilson', 'sig': 'SW-009'},
            
            # Sensor pulls
            {'barcode': 'TEMP_001A', 'qty': 10, 'qc': 'QC Inspector', 'sig': 'QCI-010'},
            
            # Connector pulls
            {'barcode': 'USB_C_001E', 'qty': 25, 'qc': 'John Smith', 'sig': 'JS-011'},
            
            # Transistor pulls
            {'barcode': 'NPN_001C', 'qty': 40, 'qc': 'Jane Doe', 'sig': 'JD-012'},
            
            # OpAmp pulls
            {'barcode': 'IC741_001D', 'qty': 15, 'qc': 'Mike Johnson', 'sig': 'MJ-013'}
        ]
        
        for i, event in enumerate(pull_events):
            # Find the box
            box = next(b for b in boxes if b.barcode == event['barcode'])
            
            # Create pull event with some time variation
            timestamp = datetime.now(timezone.utc)
            # Simulate events over the past week
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            timestamp = timestamp - timedelta(days=days_ago, hours=hours_ago)
            
            pull_event = PullEvent(
                box_id=box.id,
                quantity_pulled=event['qty'],
                qc_personnel=event['qc'],
                signature=event['sig'],
                timestamp=timestamp
            )
            db.session.add(pull_event)
            
            # Update box remaining quantity
            box.remaining_quantity -= event['qty']
        
        # Commit all changes
        db.session.commit()
        
        print("✅ Database seeded successfully!")
        print(f"Created {len(type_objects)} hardware types")
        print(f"Created {len(lot_objects)} lot numbers") 
        print(f"Created {len(boxes)} boxes")
        print(f"Created {len(pull_events)} pull events")
        print("\nSample data includes:")
        print("- Electronic components (resistors, capacitors, microcontrollers, etc.)")
        print("- Multiple lot numbers and box variations")
        print("- Realistic pull events with QC personnel signatures")
        print("- Varying remaining quantities to show different stock levels")

if __name__ == '__main__':
    seed_database()
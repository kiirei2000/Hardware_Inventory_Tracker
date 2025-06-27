import os
import logging
import json
import configparser
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
import pandas as pd
import io
import re
from functools import wraps
from urllib.parse import urlparse
import uuid
import qrcode
from PIL import Image
# Import barcode libraries with correct python-barcode structure
from barcode.codex import Code128
from barcode.writer import ImageWriter
# Word document generation
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import base64
import csv
import traceback

# Get application directory (parent of app folder for portable structure)
APP_DIR = Path(__file__).parent.parent.absolute()

# Configure logging
log_dir = APP_DIR / "data" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG)

# Configure barcode-specific logger
barcode_logger = logging.getLogger('barcode_generation')
barcode_logger.setLevel(logging.INFO)

handler = logging.FileHandler(log_dir / 'barcode_generation.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
barcode_logger.addHandler(handler)

def log_barcode_operation(operation, barcode_data, barcode_type, success, error=None):
    """Log barcode generation operations with detailed information"""
    timestamp = datetime.now().isoformat()
    if success:
        barcode_logger.info(f"{operation} - SUCCESS - Data: {barcode_data}, Type: {barcode_type}")
    else:
        barcode_logger.error(f"{operation} - FAILED - Data: {barcode_data}, Type: {barcode_type}, Error: {error}")

# Load configuration
def load_config():
    config = configparser.ConfigParser()
    config_file = APP_DIR / "config" / "settings.ini"
    if config_file.exists():
        config.read(config_file)
    else:
        # Create default config
        config['admin'] = {
            'username': 'admin',
            'password': 'admin123'
        }
        config['database'] = {
            'path': 'data/inventory.db'
        }
        config['app'] = {
            'port': '5000',
            'debug': 'false'
        }
    return config

config = load_config()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)

# Set secret key
app.secret_key = os.environ.get("SESSION_SECRET", "hardware-inventory-secret-key-2025")

# Configure database - use SQLite for portable desktop app
database_path = APP_DIR / "data" / "inventory.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Update static and template folders for portable structure
app.static_folder = str(APP_DIR / "static")
app.template_folder = str(APP_DIR / "templates")

# Ensure required directories exist
(APP_DIR / "data" / "exports").mkdir(parents=True, exist_ok=True)
(APP_DIR / "static" / "barcodes").mkdir(parents=True, exist_ok=True)

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    from models import *  # Import all models
    db.create_all()

# Add custom filter for JSON parsing
def from_json_filter(value):
    """Custom Jinja2 filter to parse JSON strings"""
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except (json.JSONDecodeError, TypeError):
        return {}

app.jinja_env.filters['from_json'] = from_json_filter

def is_safe_url(target):
    """Check if the target URL is safe for redirect"""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Please log in as admin to access this page.', 'error')
            next_page = request.url if is_safe_url(request.url) else None
            return redirect(url_for('admin_login', next=next_page))
        return f(*args, **kwargs)
    return decorated_function

def sanitize_box_id_component(component):
    """Sanitize a component for use in box ID generation"""
    if not component:
        return "UNK"
    # Remove special characters and limit length
    sanitized = re.sub(r'[^A-Za-z0-9\-_]', '', str(component))
    return sanitized[:10] if sanitized else "UNK"

def generate_box_id(hardware_type_name, lot_number_name, box_number):
    """Generate a unique box ID from components"""
    type_part = sanitize_box_id_component(hardware_type_name)
    lot_part = sanitize_box_id_component(lot_number_name)
    box_part = sanitize_box_id_component(box_number)
    
    return f"{type_part}_{lot_part}_{box_part}"

def generate_unique_barcode(length=10):
    """Generate a unique barcode checking for duplicates"""
    from models import Box
    
    max_attempts = 100
    for _ in range(max_attempts):
        # Generate random string
        barcode = str(uuid.uuid4()).replace('-', '')[:length].upper()
        
        # Check if already exists
        existing = Box.query.filter_by(barcode=barcode).first()
        if not existing:
            return barcode
    
    # Fallback to timestamp-based
    timestamp = str(int(datetime.now().timestamp()))[-length:]
    return f"BC{timestamp}"

def generate_barcode_image(barcode_data, barcode_type='qrcode', format='png'):
    """Generate barcode image and save to static/barcodes/"""
    try:
        # Ensure barcodes directory exists
        barcode_dir = APP_DIR / "static" / "barcodes"
        barcode_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{barcode_data}_{barcode_type}.{format}"
        filepath = barcode_dir / filename
        
        log_barcode_operation("generate_barcode_image", barcode_data, barcode_type, True)
        
        if barcode_type == 'qrcode':
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(barcode_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(str(filepath))
            
        elif barcode_type == 'code128':
            # Generate Code128 barcode
            code = Code128(barcode_data, writer=ImageWriter())
            # Save without extension as barcode library adds it
            filepath_no_ext = str(filepath).rsplit('.', 1)[0]
            code.save(filepath_no_ext)
            
        log_barcode_operation("generate_barcode_image", barcode_data, barcode_type, True)
        return f"barcodes/{filename}"
        
    except Exception as e:
        log_barcode_operation("generate_barcode_image", barcode_data, barcode_type, False, str(e))
        raise e

def log_action(action_type, user, box_id=None, hardware_type=None, lot_number=None, 
               previous_quantity=None, quantity_change=None, available_quantity=None,
               operator=None, qc_personnel=None, details=None):
    """Log an admin action with enhanced tracking"""
    from models import ActionLog
    
    try:
        action = ActionLog(
            action_type=action_type,
            user=user,
            box_id=box_id,
            hardware_type=hardware_type,
            lot_number=lot_number,
            previous_quantity=previous_quantity,
            quantity_change=quantity_change,
            available_quantity=available_quantity,
            operator=operator,
            qc_personnel=qc_personnel,
            details=json.dumps(details) if details else None
        )
        
        db.session.add(action)
        db.session.commit()
        
    except Exception as e:
        print(f"Error logging action: {e}")
        db.session.rollback()

def group_boxes_by_type_lot(results):
    """Group boxes by type code (first 3 digits) and type-lot combination"""
    type_groups = {}
    type_lot_groups = {}
    
    for result in results:
        try:
            # Extract type code (first 3 characters of box_id or fallback to box_id)
            type_code = result.box_id[:3] if len(result.box_id) >= 3 else result.box_id
            
            # Initialize type group
            if type_code not in type_groups:
                type_groups[type_code] = {
                    'type_name': result.hardware_type.name,
                    'total_boxes': 0,
                    'total_initial': 0,
                    'total_remaining': 0,
                    'lots': {}
                }
            
            # Type-lot combination key
            type_lot_key = f"{result.hardware_type.name}_{result.lot_number.name}"
            
            # Initialize type-lot group
            if type_lot_key not in type_lot_groups:
                type_lot_groups[type_lot_key] = {
                    'hardware_type': result.hardware_type.name,
                    'lot_number': result.lot_number.name,
                    'boxes': [],
                    'total_initial': 0,
                    'total_remaining': 0,
                    'box_count': 0
                }
            
            # Add to type group
            type_groups[type_code]['total_boxes'] += 1
            type_groups[type_code]['total_initial'] += result.initial_quantity or 0
            type_groups[type_code]['total_remaining'] += result.remaining_quantity or 0
            
            # Add lot info to type group
            lot_name = result.lot_number.name
            if lot_name not in type_groups[type_code]['lots']:
                type_groups[type_code]['lots'][lot_name] = {
                    'boxes': 0,
                    'initial': 0,
                    'remaining': 0
                }
            
            type_groups[type_code]['lots'][lot_name]['boxes'] += 1
            type_groups[type_code]['lots'][lot_name]['initial'] += result.initial_quantity or 0
            type_groups[type_code]['lots'][lot_name]['remaining'] += result.remaining_quantity or 0
            
            # Add to type-lot group
            type_lot_groups[type_lot_key]['boxes'].append(result)
            type_lot_groups[type_lot_key]['total_initial'] += result.initial_quantity or 0
            type_lot_groups[type_lot_key]['total_remaining'] += result.remaining_quantity or 0
            type_lot_groups[type_lot_key]['box_count'] += 1
            
        except Exception as e:
            print(f"Error processing result {result}: {e}")
            continue
    
    return type_groups, type_lot_groups

def calculate_inventory_stats(grouped_data):
    """Calculate summary statistics from grouped data with error handling"""
    try:
        total_types = len(grouped_data)
        total_boxes = sum(group.get('total_boxes', 0) for group in grouped_data.values())
        total_initial = sum(group.get('total_initial', 0) for group in grouped_data.values())
        total_remaining = sum(group.get('total_remaining', 0) for group in grouped_data.values())
        
        return {
            'total_types': total_types,
            'total_boxes': total_boxes,
            'total_initial': total_initial,
            'total_remaining': total_remaining,
            'utilization_rate': round(((total_initial - total_remaining) / total_initial * 100), 1) if total_initial > 0 else 0
        }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {
            'total_types': 0,
            'total_boxes': 0,
            'total_initial': 0,
            'total_remaining': 0,
            'utilization_rate': 0
        }

def build_filtered_query(type_filter=None, lot_filter=None, search_query=None):
    """Build base query with common filters - DRY helper"""
    from models import Box, HardwareType, LotNumber
    
    query = db.session.query(Box).join(HardwareType).join(LotNumber)
    
    if type_filter:
        query = query.filter(HardwareType.name.ilike(f'%{type_filter}%'))
    
    if lot_filter:
        query = query.filter(LotNumber.name.ilike(f'%{lot_filter}%'))
    
    if search_query:
        query = query.filter(
            db.or_(
                Box.box_id.ilike(f'%{search_query}%'),
                Box.barcode.ilike(f'%{search_query}%'),
                HardwareType.name.ilike(f'%{search_query}%'),
                LotNumber.name.ilike(f'%{search_query}%')
            )
        )
    
    return query

# Routes will be added here - continuing with the existing routes from the original app.py
# [All the existing routes from the original app.py file would be copied here]
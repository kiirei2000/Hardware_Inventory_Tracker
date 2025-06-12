import os
import logging
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
from werkzeug.middleware.proxy_fix import ProxyFix
import pandas as pd
import io
import re
from functools import wraps
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///inventory.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models after db initialization
from models import HardwareType, LotNumber, Box, PullEvent, ActionLog

# Add JSON filter for templates
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value) if value else {}
    except (json.JSONDecodeError, TypeError):
        return {}

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
            flash('Admin access required to manage boxes', 'error')
            next_url = request.url if is_safe_url(request.url) else url_for('manage_boxes')
            return redirect(url_for('admin_login', next=next_url))
        return f(*args, **kwargs)
    return decorated_function

def sanitize_box_id_component(component):
    """Sanitize a component for use in box ID generation"""
    # Remove special characters and replace spaces with underscores
    sanitized = re.sub(r'[^\w\-_]', '_', str(component).strip())
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    return sanitized.strip('_')

def generate_box_id(hardware_type_name, lot_number_name, box_number):
    """Generate a unique box ID from components"""
    type_clean = sanitize_box_id_component(hardware_type_name)
    lot_clean = sanitize_box_id_component(lot_number_name)
    box_clean = sanitize_box_id_component(box_number)
    return f"{type_clean}_{lot_clean}_{box_clean}"

def log_action(action_type, user, box_id=None, hardware_type=None, lot_number=None, details=None):
    """Log an admin action with enhanced tracking"""
    try:
        action_log = ActionLog()
        action_log.action_type = action_type
        action_log.user = user
        action_log.box_id = box_id
        action_log.hardware_type = hardware_type
        action_log.lot_number = lot_number
        action_log.details = json.dumps(details) if details else None
        db.session.add(action_log)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Failed to log action: {str(e)}")
        # Don't fail the main operation if logging fails
        pass

def group_boxes_by_type_lot(results):
    """Group boxes by type code (first 3 digits) and type-lot combination"""
    from collections import defaultdict
    
    type_code_groups = defaultdict(lambda: defaultdict(list))
    
    for box, type_name, lot_name in results:
        # Extract first 3 digits from type name
        type_code = type_name[:3] if len(type_name) >= 3 else type_name
        # Use tuple key to avoid collisions with | character
        type_lot_key = (type_name, lot_name)
        
        type_code_groups[type_code][type_lot_key].append({
            'box': box,
            'type_name': type_name,
            'lot_name': lot_name
        })
    
    # Calculate totals for each type-lot group - convert to plain dict
    grouped_data = {}
    for type_code, type_lot_groups in type_code_groups.items():
        grouped_data[type_code] = {}
        for type_lot_key, boxes_data in type_lot_groups.items():
            type_name, lot_name = type_lot_key  # Unpack tuple
            
            total_initial = sum(bd['box'].initial_quantity for bd in boxes_data)
            total_remaining = sum(bd['box'].remaining_quantity for bd in boxes_data)
            
            # Create string key for template compatibility
            display_key = f"{type_name}__{lot_name}"  # Use __ as separator
            grouped_data[type_code][display_key] = {
                'type_name': type_name,
                'lot_name': lot_name,
                'boxes': boxes_data,
                'total_initial': total_initial,
                'total_remaining': total_remaining,
                'box_count': len(boxes_data)
            }
    
    return grouped_data

def calculate_inventory_stats(grouped_data):
    """Calculate summary statistics from grouped data with error handling"""
    total_boxes = sum(g.get('box_count', 0)
                      for lots in grouped_data.values()
                      for g in lots.values())
    
    available_boxes = 0
    empty_boxes = 0
    negative_boxes = 0  # Track anomalous negative quantities
    
    for lots in grouped_data.values():
        for g in lots.values():
            for b in g.get('boxes', []):
                remaining = b['box'].remaining_quantity
                # Handle None or unexpected values
                if remaining is None:
                    remaining = 0
                
                if remaining > 0:
                    available_boxes += 1
                elif remaining == 0:
                    empty_boxes += 1
                else:  # negative
                    empty_boxes += 1
                    negative_boxes += 1
    
    total_remaining = sum(g.get('total_remaining', 0)
                          for lots in grouped_data.values()
                          for g in lots.values())
    
    return {
        'total_boxes': total_boxes,
        'available_boxes': available_boxes,
        'empty_boxes': empty_boxes,
        'negative_boxes': negative_boxes,
        'total_remaining': max(0, total_remaining)  # Ensure non-negative
    }

def build_filtered_query(type_filter=None, lot_filter=None, search_query=None):
    """Build base query with common filters - DRY helper"""
    query = db.session.query(
        Box,
        HardwareType.name.label('type_name'),
        LotNumber.name.label('lot_name')
    ).join(HardwareType, Box.hardware_type_id == HardwareType.id)\
     .join(LotNumber, Box.lot_number_id == LotNumber.id)
    
    # Apply filters
    if type_filter:
        query = query.filter(HardwareType.name == type_filter)
    if lot_filter:
        query = query.filter(LotNumber.name == lot_filter)
    if search_query and search_query.strip():
        search_pattern = f'%{search_query.strip()}%'
        query = query.filter(
            db.or_(
                Box.box_id.ilike(search_pattern),
                Box.barcode.ilike(search_pattern),
                HardwareType.name.ilike(search_pattern),
                LotNumber.name.ilike(search_pattern)
            )
        )
    
    return query

@app.route('/')
def index():
    """Home page with navigation options"""
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Simple admin login with security"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Simple admin credentials (in production, use proper hashed passwords)
        if username == 'admin' and password == 'admin123':
            session['is_admin'] = True
            session['admin_username'] = username
            
            # Secure redirect handling
            next_url = request.args.get('next')
            if next_url and is_safe_url(next_url):
                flash('Admin login successful', 'success')
                return redirect(next_url)
            else:
                flash('Admin login successful', 'success')
                return redirect(url_for('manage_boxes'))
        else:
            flash('Invalid admin credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    """Logout admin"""
    session.pop('is_admin', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/add_box', methods=['GET', 'POST'])
def add_box():
    """Add a new box to inventory"""
    if request.method == 'POST':
        try:
            # Get form data
            hardware_type_name = request.form.get('hardware_type', '').strip()
            new_hardware_type = request.form.get('new_hardware_type', '').strip()
            lot_number_name = request.form.get('lot_number', '').strip()
            new_lot_number = request.form.get('new_lot_number', '').strip()
            box_number = request.form.get('box_number', '').strip()
            initial_quantity = request.form.get('initial_quantity', 0)
            barcode = request.form.get('barcode', '').strip()
            operator = request.form.get('operator', '').strip()
            qc_operator = request.form.get('qc_operator', '').strip()
            
            # Validation
            errors = []
            
            # Handle hardware type
            if new_hardware_type:
                # Check if new type already exists
                existing_type = HardwareType.query.filter_by(name=new_hardware_type).first()
                if existing_type:
                    hardware_type = existing_type
                else:
                    hardware_type = HardwareType()
                    hardware_type.name = new_hardware_type
                    db.session.add(hardware_type)
                    db.session.flush()  # Get the ID without committing
            elif hardware_type_name:
                hardware_type = HardwareType.query.filter_by(name=hardware_type_name).first()
                if not hardware_type:
                    errors.append("Invalid hardware type selected")
            else:
                errors.append("Hardware type is required")
            
            # Handle lot number
            if new_lot_number:
                # Check if new lot already exists
                existing_lot = LotNumber.query.filter_by(name=new_lot_number).first()
                if existing_lot:
                    lot_number = existing_lot
                else:
                    lot_number = LotNumber()
                    lot_number.name = new_lot_number
                    db.session.add(lot_number)
                    db.session.flush()  # Get the ID without committing
            elif lot_number_name:
                lot_number = LotNumber.query.filter_by(name=lot_number_name).first()
                if not lot_number:
                    errors.append("Invalid lot number selected")
            else:
                errors.append("Lot number is required")
            
            # Validate other fields
            if not box_number:
                errors.append("Box number is required")
            
            try:
                initial_quantity = int(initial_quantity)
                if initial_quantity <= 0:
                    errors.append("Initial quantity must be greater than 0")
            except (ValueError, TypeError):
                errors.append("Initial quantity must be a valid number")
            
            if not barcode:
                errors.append("Barcode is required")
            elif Box.query.filter_by(barcode=barcode).first():
                errors.append("Barcode already exists")
            
            if not operator:
                errors.append("Operator name is required")
            
            if not qc_operator:
                errors.append("QC Operator name is required")
            
            if operator == qc_operator:
                errors.append("Operator and QC Operator cannot be the same")
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                # Preserve form data
                form_data = request.form.to_dict()
                types = HardwareType.query.all()
                lots = LotNumber.query.all()
                return render_template('add_box.html', types=types, lots=lots, form_data=form_data)
            
            # Generate box ID
            box_id = generate_box_id(hardware_type.name, lot_number.name, box_number)
            
            # Check if box ID already exists
            if Box.query.filter_by(box_id=box_id).first():
                flash("A box with this Type/Lot/Box combination already exists", 'error')
                form_data = request.form.to_dict()
                types = HardwareType.query.all()
                lots = LotNumber.query.all()
                return render_template('add_box.html', types=types, lots=lots, form_data=form_data)
            
            # Create new box
            new_box = Box()
            new_box.box_id = box_id
            new_box.hardware_type_id = hardware_type.id
            new_box.lot_number_id = lot_number.id
            new_box.box_number = box_number
            new_box.initial_quantity = initial_quantity
            new_box.remaining_quantity = initial_quantity
            new_box.barcode = barcode
            new_box.operator = operator
            new_box.qc_operator = qc_operator
            
            db.session.add(new_box)
            db.session.commit()
            
            # Log the box addition
            log_action(
                action_type='box_add',
                user=operator or 'System',
                box_id=box_id,
                hardware_type=hardware_type.name,
                lot_number=lot_number.name,
                details={
                    'initial_quantity': initial_quantity,
                    'previous_quantity': 0,
                    'quantity_change': initial_quantity,
                    'new_quantity': initial_quantity,
                    'barcode': barcode,
                    'operator': operator,
                    'qc_operator': qc_operator
                }
            )
            
            flash(f"Box {box_id} added successfully!", 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding box: {str(e)}")
            flash("An error occurred while adding the box", 'error')
    
    # GET request - show form
    types = HardwareType.query.all()
    lots = LotNumber.query.all()
    return render_template('add_box.html', types=types, lots=lots)

@app.route('/log_pull', methods=['GET', 'POST'])
def log_pull():
    """Log a pull event"""
    if request.method == 'POST':
        try:
            # Get form data
            barcode = request.form.get('barcode', '').strip()
            quantity_pulled = request.form.get('quantity_pulled', 0)
            qc_personnel = request.form.get('qc_personnel', '').strip()
            signature = request.form.get('signature', '').strip()
            
            # Validation
            errors = []
            
            if not barcode:
                errors.append("Barcode is required")
            
            try:
                quantity_pulled = int(quantity_pulled)
                # Allow negative quantities for returns
                if quantity_pulled == 0:
                    errors.append("Quantity cannot be zero")
            except (ValueError, TypeError):
                errors.append("Quantity must be a valid number")
            
            if not qc_personnel:
                errors.append("QC Personnel name is required")
            
            # Find the box
            box = None
            if barcode:
                box = Box.query.filter_by(barcode=barcode).first()
                if not box:
                    errors.append("Barcode not found in inventory")
                else:
                    # Determine if this is a pull or return
                    is_return = int(quantity_pulled) < 0
                    actual_quantity = abs(int(quantity_pulled))
                    
                    # Validate against available quantity for pulls only
                    if not is_return and actual_quantity > box.remaining_quantity:
                        errors.append(f"Cannot pull {actual_quantity} items. Only {box.remaining_quantity} available.")
                    
                    # For returns, ensure we don't exceed initial capacity
                    if is_return:
                        new_quantity = box.remaining_quantity + actual_quantity
                        if new_quantity > box.initial_quantity:
                            errors.append(f"Cannot return {actual_quantity} items. Would exceed initial capacity of {box.initial_quantity}.")
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                # Preserve form data
                form_data = request.form.to_dict()
                types = HardwareType.query.all()
                lots = LotNumber.query.all()
                return render_template('log_pull.html', types=types, lots=lots, form_data=form_data)
            
            # Determine if this is a pull or return
            is_return = quantity_pulled < 0
            actual_quantity = abs(quantity_pulled)
            
            # Update box quantity (handles both pulls and returns)
            if is_return:
                box.remaining_quantity += actual_quantity
            else:
                box.remaining_quantity -= actual_quantity
            
            # Create pull/return event log
            pull_event = PullEvent()
            pull_event.box_id = box.id
            pull_event.quantity = quantity_pulled  # Keep original sign
            pull_event.qc_personnel = qc_personnel  # Required field
            pull_event.signature = signature        # Optional field
            pull_event.mo = ""  # Not used in this function
            pull_event.operator = ""  # Not used in this function
            
            db.session.add(pull_event)
            db.session.commit()
            
            # Log the action with correct type
            action_type = 'return' if is_return else 'pull'
            hardware_type = HardwareType.query.get(box.hardware_type_id)
            lot_number = LotNumber.query.get(box.lot_number_id)
            log_action(
                action_type="pull" if not is_return else "return",
                user=qc_personnel,
                box_id=box.box_id,
                hardware_type=box.hardware_type.name if box.hardware_type else None,
                lot_number=box.lot_number.name if box.lot_number else None,
                details={
                    'quantity': actual_quantity,
                    'remaining_quantity': box.remaining_quantity,
                    'signature': signature,
                    'is_return': is_return
                }
            )
            
            # Updated flash message
            if is_return:
                flash(f"Return logged successfully! {actual_quantity} items returned. New quantity: {box.remaining_quantity}", 'success')
            else:
                flash(f"Pull event logged successfully! Remaining quantity: {box.remaining_quantity}", 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error logging pull event: {str(e)}")
            flash("An error occurred while logging the pull event", 'error')
    
    # GET request - show form
    types = HardwareType.query.all()
    lots = LotNumber.query.all()
    return render_template('log_pull.html', types=types, lots=lots)

@app.route('/log_event', methods=['GET', 'POST'])
def log_event():
    """Log pull/return event with improved validation"""
    if request.method == 'POST':
        try:
            # Get form data
            barcode = request.form.get('barcode', '').strip()
            quantity = request.form.get('quantity')
            event_type = request.form.get('event_type', '').strip().lower()
            mo = request.form.get('mo', '').strip()
            operator = request.form.get('operator', '').strip()
            qc_personnel = request.form.get('qc_personnel', '').strip()
            signature = request.form.get('signature', '').strip()
            
            # Validation
            errors = []
            
            if not barcode:
                errors.append("Barcode is required")
            
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    errors.append("Quantity must be greater than 0")
            except (ValueError, TypeError):
                errors.append("Quantity must be a valid number")
            
            if event_type not in ('pull', 'return'):
                errors.append("Invalid event type")
            
            if not mo:
                errors.append("Manufacturing Order (MO) is required")
            
            if not operator:
                errors.append("Operator name is required")
            
            if not qc_personnel:
                errors.append("QC Personnel name is required")
            
            if operator == qc_personnel:
                errors.append("Operator and QC Personnel cannot be the same")
            
            # Find the box
            box = None
            if barcode:
                box = Box.query.filter_by(barcode=barcode).first()
                if not box:
                    errors.append("Box with given barcode not found")
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return redirect(url_for('log_event'))
            
            # Calculate quantity change (positive for return, negative for pull)
            change = quantity if event_type == "return" else -quantity
            new_qty = box.remaining_quantity + change

            if new_qty < 0:
                flash("Not enough quantity in box", "danger")
                return redirect(url_for('log_event'))

            # Store previous quantity for action log
            previous_qty = box.remaining_quantity
            
            # Update box quantity
            box.remaining_quantity = new_qty
            
            # Create pull event record
            pull_event = PullEvent()
            pull_event.box_id = box.id
            pull_event.quantity = change
            pull_event.qc_personnel = qc_personnel
            pull_event.signature = signature
            pull_event.mo = mo
            pull_event.operator = operator
            
            db.session.add(pull_event)
            
            # Create action log record with proper quantity tracking
            log_action(
                action_type=event_type,
                user=operator,
                box_id=box.box_id,
                hardware_type=box.hardware_type.name,
                lot_number=box.lot_number.name,
                details={
                    'previous_quantity': previous_qty,
                    'quantity_change': abs(change),
                    'new_quantity': new_qty,
                    'mo': mo,
                    'operator': operator,
                    'qc_personnel': qc_personnel,
                    'signature': signature
                }
            )
            
            db.session.commit()
            
            flash("Event logged successfully!", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error logging event: {str(e)}")
            flash("An error occurred while logging the event", 'error')
    
    return render_template('log_event.html')

@app.route('/dashboard')
def dashboard():
    """Inventory dashboard with grouped display"""
    # Get filter parameters
    type_filter = request.args.get('type_filter', '')
    lot_filter = request.args.get('lot_filter', '')
    
    # Use DRY filter helper
    query = build_filtered_query(type_filter, lot_filter)
    
    # Order by type name first, then lot name, then box number
    results = query.order_by(HardwareType.name, LotNumber.name, Box.box_number).all()
    
    # Group boxes using helper function
    grouped_data = group_boxes_by_type_lot(results)
    
    # Calculate statistics
    total_stats = calculate_inventory_stats(grouped_data)
    
    # Get unique types and lots for filter dropdowns
    types = HardwareType.query.order_by(HardwareType.name).all()
    lots = LotNumber.query.order_by(LotNumber.name).all()
    
    return render_template('dashboard.html', 
                         grouped_data=grouped_data,
                         total_stats=total_stats,
                         types=types, 
                         lots=lots,
                         type_filter=type_filter,
                         lot_filter=lot_filter)

@app.route('/box_logs/<int:box_id>')
def box_logs(box_id):
    """View logs for a specific box"""
    box = Box.query.get_or_404(box_id)
    hardware_type = HardwareType.query.get(box.hardware_type_id)
    lot_number = LotNumber.query.get(box.lot_number_id)
    
    # Get pull events for this box (box_id in PullEvent refers to Box.id, not Box.box_id)
    pull_events = PullEvent.query.filter_by(box_id=box.id)\
                                .order_by(PullEvent.timestamp.desc()).all()
    
    return render_template('box_logs.html', 
                         box=box, 
                         hardware_type=hardware_type,
                         lot_number=lot_number,
                         pull_events=pull_events)

@app.route('/export_excel')
def export_excel():
    """Export current inventory to Excel"""
    try:
        # Get filter parameters
        type_filter = request.args.get('type_filter', '')
        lot_filter = request.args.get('lot_filter', '')
        
        # Build query
        query = db.session.query(
            Box.box_id,
            HardwareType.name.label('type_name'),
            LotNumber.name.label('lot_name'),
            Box.box_number,
            Box.initial_quantity,
            Box.remaining_quantity,
            Box.barcode,
            Box.created_at
        ).join(HardwareType, Box.hardware_type_id == HardwareType.id)\
         .join(LotNumber, Box.lot_number_id == LotNumber.id)
        
        # Apply filters
        if type_filter:
            query = query.filter(HardwareType.name == type_filter)
        if lot_filter:
            query = query.filter(LotNumber.name == lot_filter)
        
        # Execute query
        results = query.order_by(Box.box_id).all()
        
        # Convert to DataFrame
        data = []
        for result in results:
            data.append({
                'Box ID': result.box_id,
                'Hardware Type': result.type_name,
                'Lot Number': result.lot_name,
                'Box Number': result.box_number,
                'Initial Quantity': result.initial_quantity,
                'Remaining Quantity': result.remaining_quantity,
                'Barcode': result.barcode,
                'Created Date': result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else ''
            })
        
        if not data:
            flash("No data to export", 'warning')
            return redirect(url_for('dashboard'))
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Inventory']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=inventory_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error exporting Excel: {str(e)}")
        flash("An error occurred while exporting to Excel", 'error')
        return redirect(url_for('dashboard'))

@app.route('/get_box_info/<barcode>')
def get_box_info(barcode):
    """API endpoint to get box info by barcode"""
    box = Box.query.filter_by(barcode=barcode).first()
    if box:
        hardware_type = HardwareType.query.get(box.hardware_type_id)
        lot_number = LotNumber.query.get(box.lot_number_id)
        return jsonify({
            'found': True,
            'box_id': box.box_id,
            'hardware_type': hardware_type.name,
            'lot_number': lot_number.name,
            'remaining_quantity': box.remaining_quantity
        })
    else:
        return jsonify({'found': False})

@app.route('/manage_boxes')
@admin_required
def manage_boxes():
    """List and manage all boxes with grouping"""
    # Get filter parameters
    type_filter = request.args.get('type_filter', '')
    lot_filter = request.args.get('lot_filter', '')
    search_query = request.args.get('search', '')
    
    # Use DRY filter helper
    query = build_filtered_query(type_filter, lot_filter, search_query)
    
    # Order by type name first, then lot name, then box number
    results = query.order_by(HardwareType.name, LotNumber.name, Box.box_number).all()
    
    # Group boxes using helper function
    grouped_data = group_boxes_by_type_lot(results)
    
    # Calculate statistics with pre-computed lot counts for template
    total_stats = calculate_inventory_stats(grouped_data)
    
    # Pre-compute lot counts for each type code to avoid Jinja complexity
    type_code_stats = {}
    for type_code, type_lot_groups in grouped_data.items():
        type_code_stats[type_code] = {
            'lot_count': len(type_lot_groups),
            'total_boxes': sum(g.get('box_count', 0) for g in type_lot_groups.values())
        }
    
    # Get filter options
    types = HardwareType.query.order_by(HardwareType.name).all()
    lots = LotNumber.query.order_by(LotNumber.name).all()
    
    return render_template('manage_boxes.html',
                         grouped_data=grouped_data,
                         total_stats=total_stats,
                         type_code_stats=type_code_stats,
                         types=types,
                         lots=lots,
                         type_filter=type_filter,
                         lot_filter=lot_filter,
                         search_query=search_query)

@app.route('/edit_box/<int:box_id>', methods=['GET', 'POST'])
@admin_required
def edit_box(box_id):
    """Edit an existing box - FULL ADMIN ACCESS"""
    box = Box.query.get_or_404(box_id)
    hardware_type = HardwareType.query.get(box.hardware_type_id)
    lot_number = LotNumber.query.get(box.lot_number_id)
    
    if request.method == 'POST':
        try:
            # Get form data - ADMIN CAN EDIT EVERYTHING
            hardware_type_name = request.form.get('hardware_type', '').strip()
            new_hardware_type = request.form.get('new_hardware_type', '').strip()
            lot_number_name = request.form.get('lot_number', '').strip()
            new_lot_number = request.form.get('new_lot_number', '').strip()
            new_box_number = request.form.get('box_number', '').strip()
            new_barcode = request.form.get('barcode', '').strip()
            new_initial_quantity = request.form.get('initial_quantity', 0)
            new_current_quantity = request.form.get('current_quantity', 0)
            
            # Validation
            errors = []
            
            # Handle hardware type
            target_hardware_type = None
            if new_hardware_type:
                existing_type = HardwareType.query.filter_by(name=new_hardware_type).first()
                if existing_type:
                    target_hardware_type = existing_type
                else:
                    target_hardware_type = HardwareType()
                    target_hardware_type.name = new_hardware_type
                    db.session.add(target_hardware_type)
                    db.session.flush()
            elif hardware_type_name:
                target_hardware_type = HardwareType.query.filter_by(name=hardware_type_name).first()
                if not target_hardware_type:
                    errors.append("Invalid hardware type selected")
            else:
                errors.append("Hardware type is required")
            
            # Handle lot number  
            target_lot_number = None
            if new_lot_number:
                existing_lot = LotNumber.query.filter_by(name=new_lot_number).first()
                if existing_lot:
                    target_lot_number = existing_lot
                else:
                    target_lot_number = LotNumber()
                    target_lot_number.name = new_lot_number
                    db.session.add(target_lot_number)
                    db.session.flush()
            elif lot_number_name:
                target_lot_number = LotNumber.query.filter_by(name=lot_number_name).first()
                if not target_lot_number:
                    errors.append("Invalid lot number selected")
            else:
                errors.append("Lot number is required")
            
            # Validate other fields
            if not new_box_number:
                errors.append("Box number is required")
            
            if not new_barcode:
                errors.append("Barcode is required")
            elif new_barcode != box.barcode:
                existing_box = Box.query.filter_by(barcode=new_barcode).first()
                if existing_box:
                    errors.append("Barcode already exists")
            
            try:
                new_initial_quantity = int(new_initial_quantity)
                new_current_quantity = int(new_current_quantity)
                if new_initial_quantity <= 0:
                    errors.append("Initial quantity must be greater than 0")
                if new_current_quantity < 0:
                    errors.append("Current quantity cannot be negative")
                if new_current_quantity > new_initial_quantity:
                    errors.append("Current quantity cannot exceed initial quantity")
            except (ValueError, TypeError):
                errors.append("Quantities must be valid numbers")
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                form_data = request.form.to_dict()
                types = HardwareType.query.all()
                lots = LotNumber.query.all()
                return render_template('edit_box.html', box=box, hardware_type=hardware_type, 
                                     lot_number=lot_number, form_data=form_data, types=types, lots=lots)
            
            # Update box with new values
            if target_hardware_type:
                box.hardware_type_id = target_hardware_type.id
            if target_lot_number:
                box.lot_number_id = target_lot_number.id
            box.box_number = new_box_number
            box.barcode = new_barcode
            box.initial_quantity = new_initial_quantity
            box.remaining_quantity = new_current_quantity
            
            # Regenerate box_id
            if target_hardware_type and target_lot_number:
                box.box_id = generate_box_id(target_hardware_type.name, target_lot_number.name, new_box_number)
            
            db.session.commit()
            
            # Log the box edit action
            admin_user = session.get('admin_username', 'Unknown Admin')
            log_action(
                action_type='box_edit',
                user=admin_user,
                box_id=box.box_id,
                hardware_type=target_hardware_type.name if target_hardware_type else None,
                lot_number=target_lot_number.name if target_lot_number else None,
                details={
                    'new_initial_quantity': new_initial_quantity,
                    'new_current_quantity': new_current_quantity,
                    'new_barcode': new_barcode
                }
            )
            
            flash(f"Box {box.box_id} updated successfully!", 'success')
            return redirect(url_for('manage_boxes'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating box: {str(e)}")
            flash("An error occurred while updating the box", 'error')
    
    # GET request - show form
    types = HardwareType.query.all()
    lots = LotNumber.query.all()
    return render_template('edit_box.html', box=box, hardware_type=hardware_type, 
                         lot_number=lot_number, types=types, lots=lots)

@app.route('/delete_box/<int:box_id>', methods=['POST'])
@admin_required
def delete_box(box_id):
    """Delete a box and all its pull events"""
    try:
        box = Box.query.get_or_404(box_id)
        box_id_name = box.box_id
        
        # Check if box has any pull events
        pull_events_count = PullEvent.query.filter_by(box_id=box_id).count()
        
        # Delete all pull events first (due to foreign key constraint)
        PullEvent.query.filter_by(box_id=box_id).delete()
        
        # Get box details for logging before deletion
        hardware_type = HardwareType.query.get(box.hardware_type_id)
        lot_number = LotNumber.query.get(box.lot_number_id)
        
        # Delete the box
        db.session.delete(box)
        db.session.commit()
        
        # Log the box deletion action
        admin_user = session.get('admin_username', 'Unknown Admin')
        log_action(
            action_type='box_delete',
            user=admin_user,
            box_id=box_id_name,
            hardware_type=hardware_type.name if hardware_type else None,
            lot_number=lot_number.name if lot_number else None,
            details={
                'pull_events_deleted': pull_events_count,
                'initial_quantity': box.initial_quantity,
                'remaining_quantity': box.remaining_quantity
            }
        )
        
        flash(f"Box {box_id_name} and {pull_events_count} pull events deleted successfully!", 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting box: {str(e)}")
        flash("An error occurred while deleting the box", 'error')
    
    return redirect(url_for('manage_boxes'))

@app.route('/admin/action_log')
@admin_required
def action_log():
    """Admin-only action log page"""
    # Get filter parameters
    action_type_filter = request.args.get('action_type', '')
    user_filter = request.args.get('user', '')
    
    # Build query
    query = ActionLog.query
    
    # Apply filters
    if action_type_filter:
        query = query.filter(ActionLog.action_type == action_type_filter)
    if user_filter:
        query = query.filter(ActionLog.user.ilike(f'%{user_filter}%'))
    
    # Order by most recent first
    action_logs = query.order_by(ActionLog.timestamp.desc()).limit(500).all()
    
    # Get unique action types and users for filter dropdowns
    action_types = db.session.query(ActionLog.action_type).distinct().all()
    action_types = [at[0] for at in action_types]
    
    users = db.session.query(ActionLog.user).distinct().all()
    users = [u[0] for u in users]
    
    return render_template('admin_action_log.html', 
                         action_logs=action_logs,
                         action_types=action_types,
                         users=users,
                         action_type_filter=action_type_filter,
                         user_filter=user_filter)

# Create tables
with app.app_context():
    db.create_all()
    
@app.route('/healthz')
def health_check():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

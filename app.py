import os
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
from werkzeug.middleware.proxy_fix import ProxyFix
import pandas as pd
import io
import re

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
from models import HardwareType, LotNumber, Box, PullEvent

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

@app.route('/')
def index():
    """Home page with navigation options"""
    return render_template('index.html')

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
            
            # Validation
            errors = []
            
            # Handle hardware type
            if new_hardware_type:
                # Check if new type already exists
                existing_type = HardwareType.query.filter_by(name=new_hardware_type).first()
                if existing_type:
                    hardware_type = existing_type
                else:
                    hardware_type = HardwareType(name=new_hardware_type)
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
                    lot_number = LotNumber(name=new_lot_number)
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
            new_box = Box(
                box_id=box_id,
                hardware_type_id=hardware_type.id,
                lot_number_id=lot_number.id,
                box_number=box_number,
                initial_quantity=initial_quantity,
                remaining_quantity=initial_quantity,
                barcode=barcode
            )
            
            db.session.add(new_box)
            db.session.commit()
            
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
                if quantity_pulled <= 0:
                    errors.append("Quantity pulled must be greater than 0")
            except (ValueError, TypeError):
                errors.append("Quantity pulled must be a valid number")
            
            if not qc_personnel:
                errors.append("QC Personnel name is required")
            
            # Find the box
            box = None
            if barcode:
                box = Box.query.filter_by(barcode=barcode).first()
                if not box:
                    errors.append("Barcode not found in inventory")
                elif box.remaining_quantity < quantity_pulled:
                    errors.append(f"Insufficient quantity. Available: {box.remaining_quantity}")
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                # Preserve form data
                form_data = request.form.to_dict()
                types = HardwareType.query.all()
                lots = LotNumber.query.all()
                return render_template('log_pull.html', types=types, lots=lots, form_data=form_data)
            
            # Update box quantity
            box.remaining_quantity -= quantity_pulled
            
            # Create pull event log
            pull_event = PullEvent(
                box_id=box.id,
                quantity_pulled=quantity_pulled,
                qc_personnel=qc_personnel,
                signature=signature,
                timestamp=datetime.now(timezone.utc)
            )
            
            db.session.add(pull_event)
            db.session.commit()
            
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

@app.route('/dashboard')
def dashboard():
    """Inventory dashboard"""
    # Get filter parameters
    type_filter = request.args.get('type_filter', '')
    lot_filter = request.args.get('lot_filter', '')
    
    # Build query
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
    
    # Order by box_id
    boxes = query.order_by(Box.box_id).all()
    
    # Get unique types and lots for filter dropdowns
    types = HardwareType.query.order_by(HardwareType.name).all()
    lots = LotNumber.query.order_by(LotNumber.name).all()
    
    return render_template('dashboard.html', 
                         boxes=boxes, 
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
    
    # Get pull events for this box
    pull_events = PullEvent.query.filter_by(box_id=box_id)\
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

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

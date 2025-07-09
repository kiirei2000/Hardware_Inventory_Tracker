from datetime import datetime, timezone

# This will be imported from app
db = None

class HardwareType:
    """Hardware type lookup table"""
    __tablename__ = 'hardware_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<HardwareType {self.name}>'

class LotNumber(db.Model):
    """Lot number lookup table"""
    __tablename__ = 'lot_numbers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<LotNumber {self.name}>'

class Box(db.Model):
    """Box inventory table"""
    __tablename__ = 'boxes'
    
    id = db.Column(db.Integer, primary_key=True)
    box_id = db.Column(db.String(200), unique=True, nullable=False)  # Generated from Type_Lot_Box
    hardware_type_id = db.Column(db.Integer, db.ForeignKey('hardware_types.id'), nullable=False)
    lot_number_id = db.Column(db.Integer, db.ForeignKey('lot_numbers.id'), nullable=False)
    box_number = db.Column(db.String(50), nullable=False)
    initial_quantity = db.Column(db.Integer, nullable=False)
    remaining_quantity = db.Column(db.Integer, nullable=False)
    barcode = db.Column(db.String(100), unique=True, nullable=False)
    operator = db.Column(db.String(50))  # Box creation operator
    qc_personnel = db.Column(db.String(50))  # Box creation QC personnel
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    hardware_type = db.relationship('HardwareType', backref='boxes')
    lot_number = db.relationship('LotNumber', backref='boxes')
    
    def __repr__(self):
        return f'<Box {self.box_id}>'

class PullEvent(db.Model):
    """Pull event log table"""
    __tablename__ = 'pull_events'
    
    id = db.Column(db.Integer, primary_key=True)
    box_id = db.Column(db.Integer, db.ForeignKey('boxes.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # Can be negative for returns
    qc_personnel = db.Column(db.String(50), nullable=False)  # QC checker - required
    signature = db.Column(db.String(100), nullable=True)  # Optional signature
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    mo = db.Column(db.String(50))  # Manufacturing Order
    operator = db.Column(db.String(50))
    
    # Relationship
    box = db.relationship('Box', backref='pull_events')
    
    def __repr__(self):
        return f'<PullEvent {self.id} - Box {self.box_id}>'

class ActionLog(db.Model):
    """Admin action log table"""
    __tablename__ = 'action_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50), nullable=False)  # 'Pull', 'Return', 'box_add', 'box_edit', 'box_delete'
    user = db.Column(db.String(100), nullable=False)  # Admin username or operator name
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    box_id = db.Column(db.String(200))  # Box ID affected (if applicable)
    hardware_type = db.Column(db.String(100))  # Hardware type affected
    lot_number = db.Column(db.String(100))  # Lot number affected
    previous_quantity = db.Column(db.Integer)  # Quantity before the action
    quantity_change = db.Column(db.Integer)  # Amount changed (positive or negative)
    available_quantity = db.Column(db.Integer)  # Quantity after the action
    operator = db.Column(db.String(100))  # Operator who performed the action
    qc_personnel = db.Column(db.String(100))  # QC Personnel who approved/checked
    details = db.Column(db.Text)  # JSON or text details of the action
    
    @property
    def details_json(self):
        """Parse JSON details into a dictionary"""
        import json
        try:
            return json.loads(self.details or '{}')
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def __repr__(self):
        return f'<ActionLog {self.id}: {self.action_type} by {self.user}>'

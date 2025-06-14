# Hardware Inventory Tracker

## Overview

A web-based hardware inventory management system built with Flask that provides barcode/QR code scanning capabilities for tracking hardware components. The application allows users to add inventory boxes, log pull/return events, and manage stock levels through a responsive web interface optimized for tablets and mobile devices.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3.11)
- **Database**: SQLite with SQLAlchemy ORM (configured for PostgreSQL deployment)
- **Web Server**: Gunicorn for production deployment
- **Session Management**: Flask sessions with secure secret key

### Frontend Architecture
- **UI Framework**: Bootstrap 5 with custom CSS
- **Icons**: Font Awesome 6
- **JavaScript**: Vanilla JS for barcode scanning and dynamic forms
- **Responsive Design**: Mobile-first approach optimized for tablets and phones

### Database Schema
The application uses four main entities:
- **HardwareType**: Lookup table for hardware categories
- **LotNumber**: Lookup table for lot tracking
- **Box**: Main inventory tracking with quantities and barcodes
- **PullEvent**: Event logging for inventory movements (incomplete model)
- **ActionLog**: Admin audit trail (referenced but not fully implemented)

## Key Components

### Inventory Management
- **Add Box**: Form-based box creation with barcode generation
- **Log Events**: Pull/return event tracking with operator information
- **Dashboard**: Filterable inventory overview with export capabilities
- **Box Management**: Admin-level box editing and management

### Authentication & Authorization
- Simple admin authentication system using session-based login
- Admin-only routes protected with `@admin_required` decorator
- Configurable admin credentials via environment variables

### Barcode Integration
- Support for USB barcode scanners
- Browser-based camera scanning capability (JavaScript)
- Automatic barcode validation and lookup
- Barcode generation for new inventory items

### Data Export & Printing
- Excel export functionality using pandas and openpyxl
- Print-friendly templates with landscape formatting
- Barcode printing templates for inventory labels

## Data Flow

1. **Inventory Addition**: Hardware types and lot numbers are created as needed, boxes are assigned unique IDs and barcodes
2. **Event Logging**: Pull/return events update box quantities and create audit trails
3. **Dashboard Display**: Real-time inventory status with filtering and sorting
4. **Admin Operations**: Box editing, action logs, and system management

## External Dependencies

### Core Dependencies
- Flask & Flask-SQLAlchemy for web framework and ORM
- pandas & openpyxl for Excel export functionality
- python-barcode & qrcode for barcode generation
- gunicorn for production WSGI server

### Frontend Dependencies (CDN)
- Bootstrap 5 CSS framework
- Font Awesome icons
- Custom responsive CSS for mobile optimization

## Deployment Strategy

### Development Environment
- Replit-based development with PostgreSQL module
- Hot-reload enabled with Gunicorn
- SQLite fallback for local development

### Production Deployment
- Containerized deployment using Docker
- Gunicorn WSGI server configuration
- PostgreSQL database in production
- Autoscale deployment target on Replit

### Database Migration
- Auto-migration on startup (incomplete implementation)
- Models defined with SQLAlchemy ORM
- Support for both SQLite (dev) and PostgreSQL (prod)

## Changelog
- June 14, 2025. Initial setup
- June 14, 2025. Enhanced barcode functionality - Added dual barcode type support (Code128/QR), purple scan button, comprehensive print options with type selection

## User Preferences

Preferred communication style: Simple, everyday language.
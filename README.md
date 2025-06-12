A web-based hardware inventory tracker with barcode or QR code scanning support. Designed for efficient tracking, logging, and management of hardware inventory by associating each item or box with a unique barcode (or QR code) that encodes ID, type, lot number, and box number.

Features

1. Barcode/QR Code Scanning: Add and modify stock items by scanning their barcodes for quick and accurate lookup.

2. Flexible Data Model: Each inventory box or hardware item is tracked by a combination of unique ID, type, lot number, and box number.

3. Easy Stock Updates: Users can add new stock, update existing records, or log inventory pulls with a simple web form.

4. Responsive Web UI: Accessible from desktops, tablets, or mobile devices.

5. Excel Export & Printing: Export inventory logs for record-keeping or printing.

6. User Authentication (if enabled): Protect admin features and sensitive inventory operations.

Tech Stack

Backend: Python, Flask
Frontend: HTML, CSS (Bootstrap), JavaScript
Barcode Integration: Supports external USB barcode scanners and in-browser camera scanning (optional)
Database: SQLite (default, easily replaceable)

Usage

Add New Inventory: Scan a barcode or enter details (ID, type, lot, box number, quantity) to add a new box or item.
Log Pull Events: When items are taken out, scan the box and enter quantity pulled. The system auto-updates inventory.
Inventory Dashboard: View current stock, filter by type, lot, etc., and export data to Excel.

Quick Start (On Replit)

Fork or import the project into your Replit account.

Install dependencies:
pip install -r requirements.txt

Run the Flask app:
python app.py

Access the site via the provided web link.

Project Structure

<pre> <code> project-root/ ├── app.py ├── database.py ├── requirements.txt ├── static/ │ ├── css/ │ │ └── style.css │ └── js/ │ ├── scanner.js │ └── forms.js └── templates/ ├── base.html ├── dashboard.html ├── add_box.html └── log_pull.html </code> </pre>


How Barcodes Work:

Each box/item has a unique barcode encoding:
[Type]-[Lot Number]-[Box Number]-[ID/Serial]-[Quantity]
Scanning the barcode automatically fills or verifies form fields.
Barcodes can be generated freely using online tools (e.g., barcode.tec-it.com) and printed with a Zebra (GX430t) or similar printer.

Deployment

Hosted on Replit for easy access and collaboration.

(https://hardwareinventorytracker-production.up.railway.app/)
----

Can be exported and run locally or deployed to other Flask-friendly hosts (e.g., Render, PythonAnywhere, etc.).

Contributing

PRs and issues welcome!
For improvements, bugs, or suggestions, open an issue or submit a pull request.

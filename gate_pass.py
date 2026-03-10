import qrcode
import json
import os
from datetime import datetime

def generate_gate_pass_qr(permission, student, staff_name, request_host_url=""):
    """Generate a QR code for an approved gate pass and return the file path."""
    qr_dir = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)

    # Use a secure verification URL instead of raw JSON data
    verify_url = f"{request_host_url}verify/{permission.id}"

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0f3460", back_color="white")
    filename = f"gatepass_{permission.id}.png"
    filepath = os.path.join(qr_dir, filename)
    img.save(filepath)

    return f"qrcodes/{filename}"

import qrcode
from io import BytesIO

def generate_gate_pass_qr(permission, request_host_url=""):
    """Generate a QR code in memory and return a BytesIO object."""
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
    
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return img_io

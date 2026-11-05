"""Make a QR code PNG of the join URL to show on the projector.
Usage: python scripts/make_qr.py https://your-app.onrender.com [qr.png]   (needs: pip install "qrcode[pil]")"""
import sys
import qrcode

url = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "qr.png"
qrcode.make(url, box_size=14, border=3).save(out)
print("saved", out)

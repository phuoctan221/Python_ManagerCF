from coffee_shop.web_app import app

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    print(f"== QUAN LY QUAN COFFEE - WEB APP ==")
    print(f"Truy cap: http://localhost:{port}")
    print("Tai khoan: admin / admin123 hoac nhanvien1 / nv123")
    app.run(debug=debug, host='0.0.0.0', port=port)

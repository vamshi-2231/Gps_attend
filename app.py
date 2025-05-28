from flask import Flask
from db_config import mysql, init_mysql
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.employee_routes import employee_bp
from routes.attendance_routes import attendance_bp


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Setup MySQL from db_config.py
init_mysql(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(attendance_bp)

if __name__ == '__main__':
    app.run(debug=True)

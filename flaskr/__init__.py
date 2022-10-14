import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import jwt
from auth.auth import AuthError, requires_auth
from models.models import Role, setup_db, db, User
from .validate import validate_email_and_password, validate_user
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from operator import or_

ITEMS_PER_PAGE = 10
JWT_SECRET = os.environ.get('JWT_SECRET', 'abc123abc1234')


def handle_pagination(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return selection[start:end]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.debug = True
    setup_db(app)
    migrate = Migrate(app, db)
    '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app)

    '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Headers",
                             "Content-Type,Authorization,true")
        response.headers.add("Access-Control-Allow-Methods",
                             "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response

    @app.route("/users/me", methods=["GET"])
    @requires_auth('get:user')
    def get_current_user(current_user):
        return jsonify({
            "success": True,
            "message": "successfully retrieved user profile",
            "data": current_user
        })

    """ 
    register a new user to the database 
    """
    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        email = data.get('email', None)
        user_name = data.get('user_name', None)
        password = data.get('password', None)
        is_validated = validate_user(**data)
        if is_validated is not True:
            return jsonify({'success': False, 'message': 'Invalid data entry', 'error': is_validated}), 409
        test = User.query.filter(
            or_(User.email == email, User.user_name == user_name)).first()
        if test:
            return jsonify({'success': False, 'message': 'That email or username already exists'}), 409
        else:
            try:
                default_role = Role.query.filter(
                    Role.role_name == 'ROLE_USER').first()
                user = User(user_name=user_name,
                            email=email, password=generate_password_hash(password), role_id=default_role.id)
                user.insert()
                return jsonify({'success': True, 'data': user.short_repr(), 'message': 'User created successfully'}), 201
            except:
                abort(500)

    '''
    Log the user in by generating a valid JWT 
    '''
    @app.route("/login", methods=["POST"])
    def login():
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "message": "Please provide user details",
                    "data": None,
                    "error": "Bad request"
                }), 400
            # validate input
            is_validated = validate_email_and_password(
                data.get('email'), data.get('password'))
            if is_validated is not True:
                return jsonify({'success': False, 'message': 'Invalid data entry', 'error': is_validated}), 400
            user = User.login(
                data.get('email'),
                data.get('password')
            )
            if user:
                # token should expire after 24 hrs
                response = {}
                response["exp"] = datetime.utcnow() + timedelta(hours=24)
                response["token"] = jwt.encode(
                    user,
                    JWT_SECRET,
                    algorithm="HS256"
                )

                return jsonify({
                    "success": True,
                    "message": "Successfully fetched auth token",
                    "data": response
                })

            return jsonify({
                "success": False,
                "message": "Wrong email or password"
            }), 404
        except:
            abort(500)

    '''
    Create error handlers for all expected errors 
    '''
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method Not Allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable Entity"
        }), 422

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    @app.errorhandler(AuthError)
    def handle_auth_error(ex):
        response = jsonify({
            "success": False,
            "error": ex.error,
            "message": "Auth errors"
        })
        response.status_code = ex.status_code
        return response

    return app

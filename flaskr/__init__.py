from multiprocessing.dummy import Array
import os
from turtle import st
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api, Resource
import jwt
from dotenv import find_dotenv, load_dotenv
from auth.auth import AuthError, requires_auth
from flaskr.save_image import save_pic
from models.models import Arrondissement, Departement, Fonction, Media, Membre, Role, Structure, StructureMembre, TypeStructure, TypeStructure_fonction, setup_db, db, User, Region
from .validate import validate_dateformat, validate_email_and_password, validate_membre, validate_user
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from operator import or_

ITEMS_PER_PAGE = 10
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

JWT_SECRET = os.environ.get('JWT_SECRET', 'abc123abc1234')


def handle_pagination(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return selection[start:end]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = JWT_SECRET
    setup_db(app)
    migrate = Migrate(app, db)
    api = Api(app)
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

    """
    get current user information from the token
    """
    @app.route("/api/v1/users/me", methods=["GET"])
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
    @app.route('/api/v1/register', methods=['POST'])
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
    @app.route("/api/v1/login", methods=["POST"])
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
                # token should expire after 30 minutes
                response = {}
                response["exp"] = datetime.utcnow() + timedelta(minutes=30)
                response["token"] = jwt.encode(
                    user,
                    JWT_SECRET,
                    algorithm="HS256"
                )

                return jsonify({
                    "success": True,
                    "message": "Successfully logged in",
                    "data": response
                })

            return jsonify({
                "success": False,
                "message": "Wrong email or password"
            }), 404
        except:
            abort(500)

    '''
    api to manage regions
    '''
    @app.route('/api/v1/regions/<int:region_id>')
    @requires_auth('get:regions')
    def get_region_by_id(current_user, region_id):
        region = Region.query.filter_by(id=region_id).one_or_none()
        if region is None:
            abort(404)
        return jsonify({'success': True, 'data': region.json()}), 200

    @app.route('/api/v1/regions/<string:name>')
    @requires_auth('get:regions')
    def get_region_by_name(current_user, name):
        regions = Region.query.filter(
            Region.region_name.ilike(f'%{name}%')).all()
        data = []
        for region in regions:
            data.append(region.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/regions', methods=["POST"])
    @requires_auth('post:regions')
    def post_regions(current_user):
        data = request.get_json()
        if not data.get('name'):
            abort(400)
        region = Region.query.filter_by(region_name=data["name"]).one_or_none()
        if region:
            return jsonify({'success': False, 'error': 400, 'message': 'That region already exist'}), 400
        try:
            region = Region(region_name=data["name"])
            region.insert()
            return jsonify({'success': True, 'data': region.json()}), 201
        except:
            abort(500)

    @app.route('/api/v1/regions/<int:region_id>', methods=["PUT"])
    @requires_auth('put:regions')
    def put_regions(current_user, region_id):
        data = request.get_json()
        if not data.get('name'):
            abort(400)
        region = Region.query.filter_by(id=region_id).one_or_none()
        if region is None:
            abort(404)
        region_wname = Region.query.filter_by(
            region_name=data["name"]).one_or_none()
        if region_wname:
            return jsonify({'success': False, 'error': 400, 'message': 'That region already exist'}), 400
        try:
            region.region_name = data["name"]
            region.update()
            return jsonify({'success': True, 'data': region.json()}), 200
        except:
            abort(500)

    @app.route('/api/v1/regions')
    @requires_auth('get:regions')
    def get_all_regions(current_user):
        regions = Region.query.all()
        data = []
        for region in regions:
            data.append(region.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/regions/<int:region_id>/departements')
    @requires_auth('get:departements')
    def get_all_departements_by_region(current_user, region_id):
        region = Region.query.filter_by(id=region_id).one_or_none()
        if region is None:
            abort(404)
        data = []
        for departement in region.departements:
            data.append(departement.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/regions/<int:region_id>', methods=["DELETE"])
    @requires_auth('delete:regions')
    def delete_region_by_id(current_user, region_id):
        region = Region.query.filter_by(id=region_id).one_or_none()
        if region is None:
            abort(404)
        try:
            region.delete()
            return jsonify({'success': True, 'data': f'The region with the ID {region_id}'}), 200
        except:
            abort(500)

    '''
    api to manage departments
    '''
    @app.route('/api/v1/departements/<int:departement_id>')
    @requires_auth('get:departements')
    def get_departement_by_id(current_user, departement_id):
        departement = Departement.query.filter_by(
            id=departement_id).one_or_none()
        if departement is None:
            abort(404)
        return jsonify({'success': True, 'data': departement.json()}), 200

    @app.route('/api/v1/departements/<string:name>')
    @requires_auth('get:departements')
    def get_departement_by_name(current_user, name):
        departements = Departement.query.filter(
            Departement.departement_name.ilike(f'%{name}%')).all()
        data = []
        for departement in departements:
            data.append(departement.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/departements', methods=["POST"])
    @requires_auth('post:departements')
    def post_departements(current_user):
        data = request.get_json()
        name = data.get('name', None)
        region = data.get('region', None)
        if name is None or region is None:
            abort(400)
        departement = Departement.query.filter_by(
            departement_name=name).one_or_none()
        if departement:
            return jsonify({'success': False, 'error': 400, 'message': 'That departement already exist'}), 400
        try:
            departement = Departement(
                departement_name=name, region_id=region)
            departement.insert()
            return jsonify({'success': True, 'data': departement.json()}), 201
        except:
            abort(500)

    @app.route('/api/v1/departements/<int:departement_id>', methods=["PUT"])
    @requires_auth('put:departements')
    def put_departements(current_user, departement_id):
        data = request.get_json()
        name = data.get('name', None)
        region = data.get('region', None)
        if name is None or region is None:
            abort(400)
        departement = Departement.query.filter_by(
            id=departement_id).one_or_none()
        if departement is None:
            abort(404)
        departement_wname = Departement.query.filter_by(
            departement_name=name).one_or_none()
        if departement_wname:
            return jsonify({'success': False, 'error': 400, 'message': 'That Departement already exist'}), 400
        try:
            departement.departement_name = name
            departement.region_id = region
            departement.update()
            return jsonify({'success': True, 'data': departement.json()}), 200
        except:
            abort(500)

    @app.route('/api/v1/departements')
    @requires_auth('get:departements')
    def get_all_departements(current_user):
        departements = Departement.query.all()
        data = []
        for departement in departements:
            data.append(departement.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/departements/<int:departement_id>', methods=["DELETE"])
    @requires_auth('delete:departements')
    def delete_departement_by_id(current_user, departement_id):
        departement = Departement.query.filter_by(
            id=departement_id).one_or_none()
        if departement is None:
            abort(404)
        try:
            departement.delete()
            return jsonify({'success': True, 'message': f'the departement with ID {departement_id} has been deleted'}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/v1/departements/<int:departement_id>/arrondissements')
    @requires_auth('get:arrondissements')
    def get_all_arrondissements_by_departement(current_user, departement_id):
        departement = Departement.query.filter_by(
            id=departement_id).one_or_none()
        if departement is None:
            abort(404)
        data = []
        for arrondissement in departement.arrondissements:
            data.append(arrondissement.json())
        return jsonify({'success': True, 'data': data}), 200

    '''
    api to manage arrondissements
    '''
    @app.route('/api/v1/arrondissements/<int:arrondissement_id>')
    @requires_auth('get:arrondissements')
    def get_arrondissement_by_id(current_user, arrondissement_id):
        arrondissement = Arrondissement.query.filter_by(
            id=arrondissement_id).one_or_none()
        if arrondissement is None:
            abort(404)
        return jsonify({'success': True, 'data': arrondissement.json()}), 200

    @app.route('/api/v1/arrondissements/<string:name>')
    @requires_auth('get:arrondissements')
    def get_arrondissement_by_name(current_user, name):
        arrondissements = Arrondissement.query.filter(
            Arrondissement.arrondissement_name.ilike(f'%{name}%')).all()
        data = []
        for arrondissement in arrondissements:
            data.append(arrondissement.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/arrondissements', methods=["POST"])
    @requires_auth('post:arrondissements')
    def post_arrondissements(current_user):
        data = request.get_json()
        name = data.get('name', None)
        departement = data.get('departement', None)
        if name is None or departement is None:
            abort(400)
        arrondissement = Arrondissement.query.filter_by(
            arrondissement_name=name).one_or_none()
        if arrondissement:
            return jsonify({'success': False, 'error': 400, 'message': 'That arrondissement already exist'}), 400
        try:
            arrondissement = Arrondissement(
                arrondissement_name=name, departement_id=departement)
            arrondissement.insert()
            return jsonify({'success': True, 'data': arrondissement.json()}), 201
        except:
            abort(500)

    @app.route('/api/v1/arrondissements/<int:arrondissement_id>', methods=["PUT"])
    @requires_auth('put:arrondissements')
    def put_arrondissements(current_user, arrondissement_id):
        data = request.get_json()
        name = data.get('name', None)
        departement = data.get('departement', None)
        if name is None or departement is None:
            abort(400)
        arrondissement = Arrondissement.query.filter_by(
            id=arrondissement_id).one_or_none()
        if arrondissement is None:
            abort(404)
        arrondissement_wname = Arrondissement.query.filter_by(
            arrondissement_name=name).one_or_none()
        if arrondissement_wname:
            return jsonify({'success': False, 'error': 400, 'message': 'That Arrondissement already exist'}), 400
        try:
            arrondissement.arrondissement_name = name
            arrondissement.departement_id = departement
            arrondissement.update()
            return jsonify({'success': True, 'data': arrondissement.json()}), 200
        except:
            abort(500)

    @app.route('/api/v1/arrondissements')
    @requires_auth('get:arrondissements')
    def get_all_arrondissements(current_user):
        arrondissements = Arrondissement.query.all()
        data = []
        for arrondissement in arrondissements:
            data.append(arrondissement.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/arrondissements/<int:arrondissement_id>', methods=["DELETE"])
    @requires_auth('delete:arrondissements')
    def delete_arrondissement_by_id(current_user, arrondissement_id):
        arrondissement = Arrondissement.query.filter_by(
            id=arrondissement_id).one_or_none()
        if arrondissement is None:
            abort(404)
        try:
            arrondissement.delete()
            return jsonify({'success': True, 'message': f'the arrondissement with ID {arrondissement_id} has been deleted'}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    '''
    api to manage functions
    '''
    @app.route('/api/v1/fonctions/<int:fonction_id>')
    @requires_auth('get:fonctions')
    def get_fonction_by_id(current_user, fonction_id):
        fonction = Fonction.query.filter_by(
            id=fonction_id).one_or_none()
        if fonction is None:
            abort(404)
        return jsonify({'success': True, 'data': fonction.json()}), 200

    @app.route('/api/v1/fonctions/<string:name>')
    @requires_auth('get:fonctions')
    def get_fonction_by_name(current_user, name):
        fonctions = Fonction.query.filter(
            Fonction.fonction_name.ilike(f'%{name}%')).all()
        data = []
        for fonction in fonctions:
            data.append(fonction.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/fonctions', methods=["POST"])
    @requires_auth('post:fonctions')
    def post_fonctions(current_user):
        data = request.get_json()
        name = data.get('name', None)
        if name is None:
            abort(400)
        fonction = Fonction.query.filter_by(
            fonction_name=name).one_or_none()
        if fonction:
            return jsonify({'success': False, 'error': 400, 'message': 'That fonction already exist'}), 400
        try:
            fonction = Fonction(fonction_name=name)
            fonction.insert()
            return jsonify({'success': True, 'data': fonction.json()}), 201
        except:
            abort(500)

    @app.route('/api/v1/fonctions/<int:fonction_id>', methods=["PUT"])
    @requires_auth('put:fonctions')
    def put_fonctions(current_user, fonction_id):
        data = request.get_json()
        name = data.get('name', None)
        if name is None:
            abort(400)
        fonction = Fonction.query.filter_by(
            id=fonction_id).one_or_none()
        if fonction is None:
            abort(404)
        fonction_wname = Fonction.query.filter_by(
            fonction_name=name).one_or_none()
        if fonction_wname:
            return jsonify({'success': False, 'error': 400, 'message': 'That fonction already exist'}), 400
        try:
            fonction.fonction_name = name
            fonction.update()
            return jsonify({'success': True, 'data': fonction.json()}), 200
        except:
            abort(500)

    @app.route('/api/v1/fonctions')
    @requires_auth('get:fonctions')
    def get_all_fonctions(current_user):
        fonctions = Fonction.query.all()
        data = []
        for fonction in fonctions:
            data.append(fonction.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/fonctions/<int:fonction_id>', methods=["DELETE"])
    @requires_auth('delete:fonctions')
    def delete_fonction_by_id(current_user, fonction_id):
        fonction = Fonction.query.filter_by(
            id=fonction_id).one_or_none()
        if fonction is None:
            abort(404)
        try:
            fonction.delete()
            return jsonify({'success': True, 'message': f'the fonction with ID {fonction_id} has been deleted'}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    '''
    api to manage typestructures
    '''
    @app.route('/api/v1/typestructures/<int:typestructure_id>')
    @requires_auth('get:typestructures')
    def get_typestructure_by_id(current_user, typestructure_id):
        typestructure = TypeStructure.query.filter_by(
            id=typestructure_id).one_or_none()
        if typestructure is None:
            abort(404)
        return jsonify({'success': True, 'data': typestructure.json()}), 200

    @app.route('/api/v1/typestructures/<string:name>')
    @requires_auth('get:typestructures')
    def get_typestructure_by_name(current_user, name):
        typestructures = TypeStructure.query.filter(
            TypeStructure.type_structure_name.ilike(f'%{name}%')).all()
        data = []
        for typestructure in typestructures:
            data.append(typestructure.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/typestructures', methods=["POST"])
    @requires_auth('post:typestructures')
    def post_typestructures(current_user):
        data = request.get_json()
        name = data.get('name', None)
        parent = data.get('parent', None)
        parentSt = None
        if name is None:
            abort(400)
        typestructure = TypeStructure.query.filter_by(
            type_structure_name=name).one_or_none()
        if typestructure:
            return jsonify({'success': False, 'error': 400, 'message': 'That structure type already exist'}), 400
        if parent:
            parentSt = TypeStructure.query.filter_by(id=parent).one_or_none()

        try:
            typestructure = TypeStructure(type_structure_name=name)
            if parentSt:
                typestructure.parent_id = parent
            typestructure.insert()
            return jsonify({'success': True, 'data': typestructure.json()}), 201
        except:
            abort(500)

    @app.route('/api/v1/typestructures/<int:typestructure_id>', methods=["PUT"])
    @requires_auth('put:typestructures')
    def put_typestructure(current_user, typestructure_id):
        data = request.get_json()
        name = data.get('name', None)
        parent = data.get('parent', None)
        parentSt = None
        typestructure = TypeStructure.query.filter_by(
            id=typestructure_id).one_or_none()
        if typestructure is None:
            abort(404)
        if name is None:
            abort(400)
        typestructure_wname = TypeStructure.query.filter_by(
            type_structure_name=name).one_or_none()
        if typestructure_wname and typestructure.id != typestructure_id:
            return jsonify({'success': False, 'error': 400, 'message': 'That structure type already exist'}), 400
        if parent:
            parentSt = TypeStructure.query.filter_by(id=parent).one_or_none()
        try:
            typestructure.type_structure_name = name
            typestructure.parent = parentSt
            typestructure.update()
            return jsonify({'success': True, 'data': typestructure.json()}), 200
        except:
            abort(500)

    @app.route('/api/v1/typestructures')
    @requires_auth('get:typestructures')
    def get_all_typestructures(current_user):
        typestructures = TypeStructure.query.all()
        data = []
        for typestructure in typestructures:
            data.append(typestructure.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/typestructures/<int:typestructure_id>', methods=["DELETE"])
    @requires_auth('delete:typestructures')
    def delete_typestructure_by_id(current_user, typestructure_id):
        typestructure = TypeStructure.query.filter_by(
            id=typestructure_id).one_or_none()
        if typestructure is None:
            abort(404)
        try:
            typestructure.delete()
            return jsonify({'success': True, 'message': f'the structure type with ID {typestructure_id} has been deleted'}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/v1/typestructures/<int:typestructure_id>/fonctions')
    @requires_auth('get:fonctions')
    def get_all_fonctions_by_typestructure(current_user, typestructure_id):
        typestructure = TypeStructure.query.filter_by(
            id=typestructure_id).one_or_none()
        if typestructure is None:
            abort(404)
        data = []
        for fonction in typestructure.fonctions:
            data.append(fonction.jsonForTypeStructure())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/typestructures/<int:typestructure_id>/structures')
    @requires_auth('get:structures')
    def get_all_structures_by_typestructure(current_user, typestructure_id):
        typestructure = TypeStructure.query.filter_by(
            id=typestructure_id).one_or_none()
        if typestructure is None:
            abort(404)
        data = []
        for stucture in typestructure.structures:
            data.append(stucture.shortJson())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/typestructures/<int:typestructure_id>/fonctions/<int:fonction_id>', methods=["POST"])
    @requires_auth('post:typestructures')
    def add_fonction_to_typestructure(current_user, typestructure_id, fonction_id):
        data = request.get_json()
        nombre = data.get('nombre', None)
        if nombre is None:
            abort(400)
        typestructure = TypeStructure.query.filter_by(
            id=typestructure_id).one_or_none()
        if typestructure is None:
            abort(404)
        try:
            fonction = Fonction.query.filter_by(id=fonction_id).one_or_none()
            if fonction is None:
                abort(404)
            typestructureFonction = TypeStructure_fonction(
                typestructure_id=typestructure_id, fonction_id=fonction_id, nombre_position=nombre)
            typestructureFonction.insert()
            return jsonify({'success': True, 'data': typestructureFonction.json()}), 200
        except:
            abort(500)

    @app.route('/api/v1/typestructures/<int:typestructure_id>/fonctions/<int:fonction_id>', methods=["DELETE"])
    @requires_auth('delete:typestructures')
    def remove_fonction_to_typestructure(current_user, typestructure_id, fonction_id):
        typestructureFonction = TypeStructure_fonction.query.filter_by(
            typestructure_id=typestructure_id, fonction_id=fonction_id).one_or_none()
        if typestructureFonction is None:
            abort(404)
        try:
            typestructureFonction.delete()
            typestructure = TypeStructure.query.filter_by(
                id=typestructure_id).one_or_none()
            return jsonify({'success': True, 'data': typestructure.withFonctions()}), 200
        except:
            abort(500)

    '''
    here these routes are to manage structures 
    '''
    @app.route('/api/v1/structures', methods=["POST"])
    @requires_auth('post:structures')
    def creat_structures(current_user):
        data = request.get_json()
        name = data.get('name', None)
        adresse = data.get('adresse', None)
        contacts = data.get('contacts', None)
        typestructure = data.get('type', None)
        parent = data.get('parent', None)
        arrondissement = data.get('arrondissement', None)
        if name is None or adresse is None or contacts is None or typestructure is None or arrondissement is None:
            abort(400)
        if TypeStructure.getByID(typestructure) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That structure type {} doesnt exist'.format(typestructure)}), 404
        if Arrondissement.getByID(arrondissement) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That sub-division {} doesnt exist'.format(arrondissement)}), 404
        if Structure.getByName(name):
            return jsonify({'success': False, 'error': 400, 'message': 'A structure with the name << {} >> already exist'.format(name)}), 400
        try:
            structure = Structure(sturcture_name=name, structure_adresse=adresse, structure_contacts=contacts,
                                  typestructure_id=typestructure, arrondissement_id=arrondissement)
            if Structure.getByID(parent):
                structure.parent_id = parent
            structure.insert()
            return {'success': True, 'data': structure.json()}, 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/v1/structures/<int:structure_id>', methods=["PUT"])
    @requires_auth('put:structures')
    def update_structures(current_user, structure_id):
        data = request.get_json()
        name = data.get('name', None)
        adresse = data.get('adresse', None)
        contacts = data.get('contacts', None)
        typestructure = data.get('type', None)
        parent = data.get('parent', None)
        arrondissement = data.get('arrondissement', None)
        if name is None or adresse is None or contacts is None or typestructure is None or arrondissement is None:
            abort(400)
        structure = Structure.getByID(structure_id)
        if structure is None:
            abort(404)
        if TypeStructure.getByID(typestructure) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That structure type {} doesnt exist'.format(typestructure)}), 404
        if Arrondissement.getByID(arrondissement) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That sub-division {} doesnt exist'.format(arrondissement)}), 404
        if Structure.getByName(name) and structure.sturcture_name != name:
            return jsonify({'success': False, 'error': 400, 'message': 'A structure with the name << {} >> already exist'.format(name)}), 400
        try:
            structure.sturcture_name = name
            structure.structure_adresse = adresse
            structure.structure_contacts = contacts
            structure.typestructure_id = typestructure
            structure.arrondissement_id = arrondissement
            if Structure.getByID(parent):
                structure.parent_id = parent
            structure.update()
            return {'success': True, 'data': structure.json()}, 201
        except Exception as e:
            return jsonify({'success': False, "error": 500, 'message': str(e)}), 500

    @app.route('/api/v1/structures')
    @requires_auth('get:structures')
    def get_all_structures(current_user):
        structures = Structure.query.all()
        data = []
        for structure in structures:
            data.append(structure.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/structures/<int:structure_id>', methods=["DELETE"])
    @requires_auth('delete:structures')
    def delete_structure_by_id(current_user, structure_id):
        structure = Structure.query.filter_by(
            id=structure_id).one_or_none()
        if structure is None:
            abort(404)
        try:
            structure.delete()
            return jsonify({'success': True, 'message': f'the structure with ID {structure_id} has been deleted'}), 200
        except Exception as e:
            return jsonify({'success': False, "error": 500, 'message': str(e)}), 500

    @app.route('/api/v1/structures/<int:structure_id>')
    @requires_auth('get:structures')
    def get_structure_by_id(current_user, structure_id):
        structure = Structure.query.filter_by(
            id=structure_id).one_or_none()
        if structure is None:
            abort(404)
        return jsonify({'success': True, 'data': structure.jsonWithParent(), 'medias': structure.mediasJson(), 'substructures': structure.subStructureJson()}), 200

    @app.route('/api/v1/structures/<string:name>')
    @requires_auth('get:structures')
    def get_structure_by_name(current_user, name):
        structures = Structure.query.filter(
            Structure.structure_name.ilike(f'%{name}%')).all()
        data = []
        for structure in structures:
            data.append(structure.json())
        return jsonify({'success': True, 'data': data}), 200

    @app.route('/api/v1/structures/<int:structure_id>/medias', methods=['POST'])
    @requires_auth('put:structures')
    def set_structure_media(current_user, structure_id):
        if not request.files["structure_image"]:
            abort(400)
        structure = Structure.getByID(structure_id)
        if structure is None:
            abort(400)
        try:
            file_name = save_pic(
                request.files["structure_image"], avatar=False)
            file_path = request.host_url+"static/images/autres/"+file_name
            media = Media(file_name=file_name, path_name=file_path,
                          type_media='IMAGE', structure_id=structure_id)
            media.insert()
            return jsonify({'success': True, 'data': structure.json()}), 200
        except Exception as e:
            return jsonify({'success': False, "error": 500, 'message': str(e)}), 500

    @app.route('/api/v1/structures/<int:structure_id>/medias/<int:media_id>', methods=['DELETE'])
    @requires_auth('put:structures')
    def remove_structure_media(current_user, structure_id, media_id):
        structure = Structure.getByID(structure_id)
        media = Media.getByID(media_id)

        if structure is None:
            abort(400)
        if media is None:
            abort(400)
        try:
            structure.medias.remove(media)
            structure.update()
            os.remove(os.path.join(app.root_path,
                      "static/images/autres", media.file_name))
            return jsonify({'success': True, 'data': structure.json()}), 200
        except Exception as e:
            return jsonify({'success': False, "error": 500, 'message': str(e)}), 500

    """ 
    Manage members 
    """
    @app.route('/api/v1/membres', methods=["POST"])
    @requires_auth('post:membres')
    def create_membres(current_user):
        data = request.get_json()
        membre_fullname = data.get('fullname', None)
        membre_genre = data.get('genre', None)
        membre_dob = data.get('dob', None)
        membre_pob = data.get('pob', None)
        membre_mother = data.get('mother', None)
        membre_father = data.get('father', None)
        status_matrimonial = data.get('statusm', None)
        membre_conjoint = data.get('conjoint', None)
        membre_nbenfant = data.get('nbenfant', None)
        membre_contacts = data.get('contacts', None)
        membre_adresse = data.get('adresse', None)
        user_id = data.get('userid', None)
        arrondissement_id = data.get('arrondissement', None)

        is_validated = validate_membre(**data)
        if is_validated is not True:
            return jsonify({'success': False, 'message': 'Invalid data entry', 'error': is_validated}), 409
        if Arrondissement.getByID(arrondissement_id) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That sub-division {} doesnt exist'.format(arrondissement_id)}), 404
        if Membre.getByUserID(user_id):
            return jsonify({'success': False, 'error': 400, 'message': 'That account is already linked to another membre'}), 400
        try:
            membre = Membre(membre_fullname=membre_fullname, membre_genre=membre_genre, membre_dob=membre_dob, membre_pob=membre_pob, membre_father=membre_father,
                            membre_mother=membre_mother, membre_adresse=membre_adresse, membre_contacts=membre_contacts, arrondissement_id=arrondissement_id,
                            membre_conjoint=membre_conjoint, membre_nbenfant=membre_nbenfant, status_matrimonial=status_matrimonial, user_id=user_id)
            membre.insert()
            return {'success': True, 'data': membre.json()}, 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/v1/membres/<int:membre_id>', methods=["PUT"])
    @requires_auth('put:membres')
    def update_membres(current_user, membre_id):
        data = request.get_json()
        membre_fullname = data.get('fullname', None)
        membre_genre = data.get('genre', None)
        membre_dob = data.get('dob', None)
        membre_pob = data.get('pob', None)
        membre_mother = data.get('mother', None)
        membre_father = data.get('father', None)
        status_matrimonial = data.get('statusm', None)
        membre_conjoint = data.get('conjoint', None)
        membre_nbenfant = data.get('nbenfant', None)
        membre_contacts = data.get('contacts', None)
        membre_adresse = data.get('adresse', None)
        user_id = data.get('userid', None)
        arrondissement_id = data.get('arrondissement', None)

        is_validated = validate_membre(**data)
        if is_validated is not True:
            return jsonify({'success': False, 'message': 'Invalid data entry', 'error': is_validated}), 409
        if Arrondissement.getByID(arrondissement_id) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That sub-division {} doesnt exist'.format(arrondissement_id)}), 404
        membre = Membre.getByID(membre_id)
        if membre is None:
            abort(404)
        try:
            membre.membre_fullname = membre_fullname
            membre.membre_genre = membre_genre
            membre.membre_dob = membre_dob
            membre.membre_pob = membre_pob
            membre.membre_father = membre_father
            membre.membre_mother = membre_mother
            membre.membre_adresse = membre_adresse
            membre.membre_contacts = membre_contacts
            membre.arrondissement_id = arrondissement_id
            membre.membre_conjoint = membre_conjoint
            membre.membre_nbenfant = membre_nbenfant
            membre.status_matrimonial = status_matrimonial
            membre.user_id = user_id
            membre.update()
            return {'success': True, 'data': membre.json()}, 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/v1/membres/<int:membre_id>', methods=["PATCH"])
    @requires_auth('put:membres')
    def consecration_membres(current_user, membre_id):
        data = request.get_json()
        paroisse_id = data.get('paroisse', None)
        date_consecration = data.get('date_consecration', None)
        if not validate_dateformat(date_consecration):
            return jsonify({'success': False, 'error': 400, 'message': 'The date {} is an invalid date'.format(date_consecration)}), 400
        if Structure.getByID(paroisse_id) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That structure {} doesnt exist'.format(paroisse_id)}), 404
        membre = Membre.getByID(membre_id)
        if membre is None:
            abort(404)
        try:
            membre.paroisse_consecration_id = paroisse_id
            membre.date_consecration = date_consecration
            membre.update()
            return {'success': True, 'data': membre.json()}, 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/v1/membres/<int:membre_id>/structures', methods=["POST"])
    @requires_auth('put:membres')
    def structures_membres(current_user, membre_id):
        data = request.get_json()
        structure_id = data.get('structure_id', None)
        date_affectation = data.get('date_affectation', None)
        fonction_id = data.get('fonction_id', None)
        actuel = data.get('actuel', False)
        if not validate_dateformat(date_affectation):
            return jsonify({'success': False, 'error': 400, 'message': 'The date {} is an invalid date'.format(date_affectation)}), 400
        if Structure.getByID(structure_id) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That structure {} doesnt exist'.format(structure_id)}), 404
        if Fonction.getByID(fonction_id) is None:
            return jsonify({'success': False, 'error': 404, 'message': 'That Fonction {} doesnt exist'.format(fonction_id)}), 404

        membre = Membre.getByID(membre_id)
        if membre is None:
            abort(404)
        try:
            structure_membre = StructureMembre(
                membre_id=membre_id, structure_id=structure_id, fonction_id=fonction_id, date_affectation=date_affectation, actuel=actuel)
            structure_membre.insert()
            return {'success': True, 'data': membre.json()}, 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/v1/membres/<int:membre_id>/medias', methods=['POST'])
    @requires_auth('put:membres')
    def set_membres_avatar(current_user, membre_id):
        if not request.files["membre_image"]:
            abort(400)
        membre = Membre.getByID(membre_id)
        if membre is None:
            abort(404)
        try:
            file_name = save_pic(request.files["membre_image"])
            file_path = request.host_url+"static/images/avatars/"+file_name
            media = Media(file_name=file_name,
                          path_name=file_path, type_media='IMAGE')
            media.avatar_membre = membre
            media.insert()
            return jsonify({'success': True, 'data': membre.json()}), 200
        except Exception as e:
            return jsonify({'success': False, "error": 500, 'message': str(e)}), 500

    @app.route('/api/v1/membres/<int:membre_id>/medias/<int:media_id>', methods=['DELETE'])
    @requires_auth('put:membres')
    def remove_membre_media(current_user, membre_id, media_id):
        media = Media.getByID(media_id)
        membre = Membre.getByID(membre_id)
        if membre is None:
            abort(404)
        if media is None:
            abort(400)
        try:
            membre.avatar = None
            media.delete()
            os.remove(os.path.join(app.root_path,
                      "static/images/avatars", media.file_name))
            return jsonify({'success': True, 'data': membre.json()}), 200
        except Exception as e:
            return jsonify({'success': False, "error": 500, 'message': str(e)}), 500

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

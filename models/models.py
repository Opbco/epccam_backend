from datetime import datetime, timedelta
from time import timezone
from sqlalchemy import Column, String, Integer, Boolean, Text, func
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash

database_name = "epccam"
database_path = "postgresql://postgres:OPBco@{}/{}".format(
    'localhost:5432', database_name)

db = SQLAlchemy()

'''
setup_db(app)
    binds a flask application and a SQLAlchemy service
'''


def setup_db(app, database_path=database_path):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)


'''
User
a persistent user entity, extends the base SQLAlchemy Model
'''


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_name = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role_id = Column(Integer, db.ForeignKey('roles.id'), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    membre = db.relationship('Membre', backref='user', lazy=True)
    programmations = db.relationship(
        'Programmation', backref='user', lazy=True)
    actualites = db.relationship(
        'Actualite', backref='user', lazy=True)

    """Get a active user by email"""
    @staticmethod
    def get_by_email(email):
        return User.query.filter(User.email == email, User.active == True).one_or_none()

    """Login a user"""
    @staticmethod
    def login(email, password):
        user = User.get_by_email(email)
        if user is None or not check_password_hash(user.password, password):
            return
        return {'exp': datetime.utcnow() + timedelta(minutes=30), 'userid': user.id, 'username': user.user_name, 'email': user.email, 'role_name': user.role.role_name, 'permissions': user.role.permissions}

    def short_repr(self):
        return {'userid': self.id, 'username': self.user_name, 'email': self.email, 'role_name': self.role.role_name, 'permissions': self.role.permissions}

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<User ID: {self.id} UserName: {self.user_name} Email: {self.email} >'


class Role(db.Model):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    role_name = Column(String, unique=True, nullable=False)
    role_description = Column(String, nullable=True)
    permissions = Column(db.ARRAY(String), nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<Role ID: {self.id} RoleName: {self.role_name} >'


class Region(db.Model):
    __tablename__ = 'regions'
    id = Column(Integer, primary_key=True)
    region_name = Column(String, unique=True, nullable=False)
    departements = db.relationship('Departement', backref='region', lazy=True)

    def json(self):
        return {'id': self.id, 'name': self.region_name}

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<Region ID: {self.id} Name: {self.region_name} >'


class Departement(db.Model):
    __tablename__ = 'departements'
    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, db.ForeignKey('regions.id'), nullable=False)
    departement_name = Column(String, unique=True, nullable=False)
    arrondissements = db.relationship(
        'Arrondissement', backref='departement', lazy=True)

    def json(self):
        return {'id': self.id, 'name': self.departement_name, 'region': self.region.json()}

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<Departement ID: {self.id} Name: {self.departement_name} >'


class Arrondissement(db.Model):
    __tablename__ = 'arrondissements'
    id = Column(Integer, primary_key=True)
    departement_id = Column(Integer, db.ForeignKey(
        'departements.id'), nullable=False)
    arrondissement_name = Column(String, nullable=False)
    structures = db.relationship(
        'Structure', backref='arrondissement', lazy=True)

    def json(self):
        return {'id': self.id, 'name': self.arrondissement_name, 'departement': self.departement.json()}

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    @classmethod
    def getByID(cls, _id):
        find = cls.query.filter_by(id=_id).one_or_none()
        return find

    def __repr__(self):
        return f'<Arrondissement ID: {self.id} Name: {self.arrondissement_name} >'


class Fonction(db.Model):
    __tablename__ = 'fonctions'
    id = Column(Integer, primary_key=True)
    fonction_name = Column(String, unique=True, nullable=False)
    typestructures = db.relationship(
        "TypeStructure_fonction", back_populates="fonction")
    membres = db.relationship("StructureMembre", backref="fonction")

    def json(self):
        return {'id': self.id, 'name': self.fonction_name}

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    @classmethod
    def getByID(cls, _id):
        find = cls.query.filter_by(id=_id).one_or_none()
        return find

    def __repr__(self):
        return f'<Fonction ID: {self.id} Name: {self.fonction_name} >'


class TypeStructure(db.Model):
    __tablename__ = 'typestructures'
    id = Column(Integer, primary_key=True)
    type_structure_name = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, db.ForeignKey(
        'typestructures.id', onupdate="CASCADE", ondelete="CASCADE"), index=True)
    sub_typeStructure = db.relationship(
        "TypeStructure", backref=db.backref("parent", remote_side=[id]))
    fonctions = db.relationship(
        "TypeStructure_fonction", back_populates="typestructure")
    structures = db.relationship(
        'Structure', backref='typestructure', lazy=True)

    def json(self):
        if not self.parent_id:
            return {'id': self.id, 'name': self.type_structure_name, 'parent': None}
        return {'id': self.id, 'name': self.type_structure_name, 'parent': self.parent.json()}

    def withFonctions(self):
        fonctionsJson = []
        for fonction in self.fonctions:
            fonctionsJson.append(fonction.jsonForTypeStructure())
        if not self.parent_id:
            return {'id': self.id, 'name': self.type_structure_name, 'parent': None, 'fonctions': fonctionsJson}
        return {'id': self.id, 'name': self.type_structure_name, 'parent': self.parent.json(), 'fonctions': fonctionsJson}

    @classmethod
    def getByID(cls, _id):
        find = cls.query.filter_by(id=_id).one_or_none()
        return find

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<TypeStructure ID: {self.id} Name: {self.type_structure_name} >'


class TypeStructure_fonction(db.Model):
    __tablename__ = 'typeStructure_fonction'
    typestructure_id = Column(Integer, db.ForeignKey(
        'typestructures.id'), primary_key=True)
    fonction_id = Column(Integer, db.ForeignKey(
        'fonctions.id'), primary_key=True)
    nombre_position = Column(Integer, nullable=False)
    typestructure = db.relationship(
        "TypeStructure", back_populates="fonctions")
    fonction = db.relationship("Fonction", back_populates="typestructures")

    def json(self):
        return {'typestructure': self.typestructure.json(), 'fonction': self.fonction.json(), 'nombre': self.nombre_position}

    def jsonForTypeStructure(self):
        return {'fonction': self.fonction.json(), 'nombre': self.nombre_position}

    def jsonForTypeFonction(self):
        return {'typestructure': self.typestructure.json(), 'nombre': self.nombre_position}

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()


class Structure(db.Model):
    __tablename__ = 'structures'
    id = Column(Integer, primary_key=True)
    sturcture_name = Column(String, unique=True, nullable=False)
    structure_adresse = Column(String, nullable=True)
    structure_contacts = Column(String, nullable=False)
    nombre_communicant = Column(Integer, nullable=True, default=0)
    nombre_baptise = Column(Integer, nullable=False, default=0)
    date_creation = Column(db.DateTime(timezone=True),
                           server_default=func.now())
    typestructure_id = Column(Integer, db.ForeignKey(
        'typestructures.id'), nullable=False)
    arrondissement_id = Column(Integer, db.ForeignKey(
        'arrondissements.id'), nullable=False)
    statistiques = db.relationship(
        'Statistique', backref='structure', lazy=True)
    consacrete_membres = db.relationship(
        'Membre', backref='paroisse_consacrete', lazy=True)
    membres = db.relationship("StructureMembre", back_populates="structure")
    medias = db.relationship("Media", backref='structure', lazy=True)
    actualites = db.relationship("Actualite", backref='structure', lazy=True)
    programmations = db.relationship(
        "Programmation", backref='structure', lazy=True)
    parent_id = Column(Integer, db.ForeignKey(
        'structures.id', onupdate="CASCADE", ondelete="CASCADE"), index=True)
    sub_structures = db.relationship(
        "Structure", backref=db.backref("parent", remote_side=[id]))

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def shortJson(self):
        if self.parent_id:
            return {'id': self.id, 'name': self.sturcture_name, 'adresse': self.structure_adresse, 'contacts': self.structure_contacts, 'parent': self.parent.json()}
        return {'id': self.id, 'name': self.sturcture_name, 'adresse': self.structure_adresse, 'contacts': self.structure_contacts}

    def jsonWithParent(self):
        if self.parent_id:
            return {'parent': self.parent.shortJson(), 'id': self.id, 'name': self.sturcture_name, 'adresse': self.structure_adresse, 'contacts': self.structure_contacts, 'nombre_communicant': self.nombre_communicant, 'nombre_baptise': self.nombre_baptise, 'type': self.typestructure.json(), 'arrondissement': self.arrondissement.json()}
        return {'id': self.id, 'name': self.sturcture_name, 'adresse': self.structure_adresse, 'contacts': self.structure_contacts, 'nombre_communicant': self.nombre_communicant, 'nombre_baptise': self.nombre_baptise, 'type': self.typestructure.json(), 'arrondissement': self.arrondissement.json()}

    def json(self):
        return {'id': self.id, 'name': self.sturcture_name, 'adresse': self.structure_adresse, 'contacts': self.structure_contacts, 'nombre_communicant': self.nombre_communicant, 'nombre_baptise': self.nombre_baptise, 'type': self.typestructure.json(), 'arrondissement': self.arrondissement.json(), 'medias': self.mediasJson()}

    def subStructureJson(self):
        data = []
        for structure in self.sub_structures:
            data.append(structure.json())
        return data

    def mediasJson(self):
        data = []
        for media in self.medias:
            data.append(media.json())
        return data

    @classmethod
    def getByID(cls, structure_id):
        structure = cls.query.filter_by(id=structure_id).one_or_none()
        return structure

    @classmethod
    def getByName(cls, name):
        structure = cls.query.filter_by(sturcture_name=name).one_or_none()
        return structure

    def __repr__(self):
        return f'<TypeStructure ID: {self.id} Name: {self.sturcture_name} >'


class Membre(db.Model):
    __tablename__ = 'membres'
    id = Column(Integer, primary_key=True)
    membre_fullname = Column(String, unique=True, nullable=False)
    membre_genre = Column(db.Enum('M', 'F', name='genreTypes'),
                          nullable=False, server_default='M')
    membre_dob = Column(db.DateTime, nullable=False)
    membre_pob = Column(String, nullable=False)
    membre_mother = Column(String, nullable=False)
    membre_father = Column(String, nullable=False)
    status_matrimonial = Column(db.Enum('M', 'C', 'V', name='maritalTypes'),
                                nullable=False, server_default='C')
    membre_conjoint = Column(String, nullable=False)
    membre_nbenfant = Column(Integer, nullable=False, default=0)
    membre_adresse = Column(String, nullable=False)
    membre_contacts = Column(String, nullable=False)
    date_consecration = Column(db.DateTime(timezone=True), nullable=True)
    date_created = Column(db.DateTime(timezone=True),
                          server_default=func.now())
    date_updated = Column(db.DateTime(timezone=True),
                          onupdate=func.now())
    typestructure_id = Column(Integer, db.ForeignKey(
        'typestructures.id'), nullable=True)
    arrondissement_id = Column(Integer, db.ForeignKey(
        'arrondissements.id'), nullable=False)
    paroisse_consecration_id = Column(
        Integer, db.ForeignKey('structures.id'), nullable=True)
    media_id = Column(Integer, db.ForeignKey('medias.id'), nullable=True)
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    structures = db.relationship("StructureMembre", back_populates="membre")

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    @classmethod
    def getByID(cls, membre_id):
        membre = cls.query.filter_by(id=membre_id).one_or_none()
        return membre

    @classmethod
    def getByUserID(cls, user_id):
        membre = cls.query.filter_by(user_id=user_id).one_or_none()
        return membre

    def myStructures(self):
        structures = db.session.query(StructureMembre).join(
            Membre, StructureMembre.membre_id == Membre.id).order_by(db.desc(StructureMembre.date_affectation), StructureMembre.actuel).all()
        data = [structuremembre.structure.json()
                for structuremembre in structures]
        return data

    def json(self):
        return {
            'id': self.id,
            'fullname': self.membre_fullname,
            'genre': self.membre_genre,
            'dob': self.membre_dob,
            'pob': self.membre_pob,
            'mother': self.membre_mother,
            'father': self.membre_father,
            'statusm': self.status_matrimonial,
            'conjoint': self.membre_conjoint,
            'nbenfant': self.membre_nbenfant,
            'contacts': self.membre_contacts,
            'adresse': self.membre_adresse,
            'arrondissement': self.arrondissement.json(),
            'date_consecration': self.date_consecration,
            'consecratoire': self.paroisse_consacrete.json(),
            'avatar': self.avatar.json(),
            'structures': self.myStructures()
        }

    def __repr__(self):
        return f'<Membre ID: {self.id} Name: {self.membre_fullname} >'


class Media(db.Model):
    __tablename__ = 'medias'
    id = Column(Integer, primary_key=True)
    file_name = Column(String, unique=True, nullable=False)
    path_name = Column(String, unique=True, nullable=False)
    type_media = Column(db.Enum('IMAGE', 'VIDEO', 'DOC', name='mediaTypes'),
                        nullable=False, server_default='IMAGE')
    date_created = Column(db.DateTime(timezone=True),
                          server_default=func.now())
    date_updated = Column(db.DateTime(timezone=True),
                          onupdate=func.now())
    avatar_membre = db.relationship('Membre', backref='avatar', lazy=True)
    structure_id = Column(Integer, db.ForeignKey(
        'structures.id'), nullable=True)

    def json(self):
        return {'id': self.id, 'file_name': self.file_name, 'file_url': self.path_name, 'type': self.type_media, 'created_on': self.date_created}

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    @classmethod
    def getByID(cls, media_id):
        media = cls.query.filter_by(id=media_id).one_or_none()
        return media

    def __repr__(self):
        return f'<Media ID: {self.id} Name: {self.file_name} >'


class StructureMembre(db.Model):
    __tablename__ = 'structuremembres'
    structure_id = Column(Integer, db.ForeignKey(
        'structures.id', ondelete="CASCADE"), primary_key=True)
    membre_id = Column(Integer, db.ForeignKey(
        'membres.id', ondelete="CASCADE"), primary_key=True)
    actuel = Column(Boolean, nullable=False, default=True)
    date_affectation = Column(db.DateTime(timezone=True), nullable=False)
    fonction_id = Column(Integer, db.ForeignKey(
        'fonctions.id'), nullable=False)
    structure = db.relationship(
        "Structure", back_populates="membres")
    membre = db.relationship("Membre", back_populates="structures")

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<StructureMembre ID: {self.id} structure: {self.structure_id} membre: {self.membre_id} fonction: {self.fonction_id} >'


class Programmation(db.Model):
    __tablename__ = 'programmations'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    date_created = Column(db.DateTime(timezone=True),
                          server_default=func.now())
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    structure_id = Column(Integer, db.ForeignKey(
        'structures.id'), nullable=False)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<Programmation ID: {self.id} Title: {self.title} >'


class Actualite(db.Model):
    __tablename__ = 'actualites'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    details = Column(Text, nullable=False)
    status = Column(Boolean, nullable=False, default=False)
    date_created = Column(db.DateTime(timezone=True),
                          server_default=func.now())
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    structure_id = Column(Integer, db.ForeignKey(
        'structures.id'), nullable=False)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<Actualite ID: {self.id} Title: {self.title} >'


class Statistique(db.Model):
    __tablename__ = 'statistiques'
    id = Column(Integer, primary_key=True)
    nombre_baptise = Column(Integer, nullable=False, default=0)
    annee_scolaire = Column(String(4), nullable=False)
    structure_id = Column(Integer, db.ForeignKey(
        'structures.id'), nullable=False)
    nombre_consacre = Column(Integer, nullable=False, default=0)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return f'<Statistique ID: {self.id} StructureID: {self.structure_id} >'

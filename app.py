import os
#import secrets

from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from blocklist import BLOCKLIST
from db import db
import models

from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint

def create_app(db_url=None):
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True #Any exceptions hidden inside the extension of falsk will be propogated to the main app so we can see it
    app.config["API_TITLE"] = "Store REST API"#Titile of the API in the documentaiton
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3" #Standard for API documentation 
    app.config["OPENAPI_URL_PREFIX"] = "/" #telling flask where the root of the API is
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui" #Tells the flask to use swagger for the documentation
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/" # the source to get swagger code
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL","sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATION"]=False
    api = Api(app)#connects flask_smorest extension to flask app
    db.init_app(app)
    migrate = Migrate(app,db)
    # secret key = secrets.SystemRandom().getrandbits(length of the number in bits)
    app.config["JWT_SECRET_KEY"] = "252624807248722732859324183230006139351"
    jwt = JWTManager(app)
    
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {"description":"The token has been revoked.","error":"token_revoked"}
            ),
            401,
        )
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {"description":"The token is not fresh.",
                 "error":"fresh_token_required"}
            ),
            401,
        )
    
    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        if int(identity)==1:
            return {"is_admin":True}
        return {"is_admin":False}
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return(
            jsonify({
                "message" : "The token has expired." , "error" : "invalid_token"
            }),401,
        )
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return(
            jsonify({"message":"Signature verification failed.","error":"invalid_token"}
                    ),
            401,
        )
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return(
            jsonify(
                {"description":"Request does not contain an access token.","error": "authoriation_required"},
            ),
            401,
        )
    
    with app.app_context():
         db.create_all()

    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)
    
    return app


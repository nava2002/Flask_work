import requests
import os
from dotenv import load_dotenv
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_jwt_extended import create_access_token,create_refresh_token,get_jwt_identity, jwt_required, get_jwt
from flask import current_app

from blocklist import BLOCKLIST
from db import db
from models import UserModel
from schemas import UserSchema, UserRegisterSchema
from tasks import send_user_registration_email

blp = Blueprint("Users", "users", description="Operations related to users.")


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    def post(self,user_data):
        user = UserModel(
            username=user_data["username"],
            email=user_data["email"],
            password=pbkdf2_sha256.hash(user_data["password"])
        )
        try:
            db.session.add(user)
            db.session.commit()
            
            current_app.queue.enqueue(send_user_registration_email,user.email,user.username)
                       
        except IntegrityError:
            abort(409,message="A user with that username already exist.")
        except SQLAlchemyError as e:
            abort(500,message=str(e))
        return {"message":"The user was registered successfully registered."}, 200
    

@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()
        
        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=str(user.id),fresh=True)
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {"access_token":access_token,"refresh_token":refresh_token}
        
        abort(401,message="Invalid Credentials.")
        
@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token":new_token}

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return{"message":"You have successfully logged out."}

@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self,user_id):
        user = UserModel.query.get_or_404(user_id)
        return user
    
    def delete(self,user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message":"User deleted."}, 200    
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import ItemModel
from schemas import ItemSchema, ItemUpdateSchema

blp = Blueprint("Items", __name__,description="Operations on items")

@blp.route("/item/<int:item_id>")
class Item(MethodView):
    @jwt_required()
    @blp.response(200,ItemSchema)
    def get(self,item_id):
         item = ItemModel.query.get_or_404(item_id)
         return item   
    
    @jwt_required()
    def delete(self,item_id):
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401,message="Admin privilage required.")
        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message":"Item deleted sucessfully."}
    
    @jwt_required()        
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200,ItemSchema)        
    def put(self, item_data, item_id):
        #item_data = request.get_json() -> not needed coz of validation through marshmallow
        #The presence of the parmaeters such as name and price is checked through ItemUpdateSchema
        item = ItemModel.query.get(item_id)
        if item:
            item.price = item_data["price"]
            item.name = item_data["name"]
        else:
            item = ItemModel(id=item_id, **item_data)
        
        db.session.add(item)
        db.session.commit()
        
        return item

@blp.route("/item")
class ItemList(MethodView):
    @blp.response(200,ItemSchema(many=True))
    def get(self):
        #return {"items":list(items.values())} -> when many=True then its already gets converted to a list
        return ItemModel.query.all()
    
    @jwt_required()
    @blp.arguments(ItemSchema)
    @blp.response(201,ItemSchema)
    def post(self,item_data):
        #item_data = request.get_json() -> not needed coz the validated jason payload is recived through the ItemSchema
        #ensuring if all the data is there in the JSON payload
        #The above condition is checked using marshmallow schemas
        #ensuring that if an item like this already exist
        #Now that we have a database we can leave the uniqueness of a value chceking to the database and modify the remaing code
        item = ItemModel(**item_data)
        
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500,message="An error occured wile inserting the item")
        return item,201
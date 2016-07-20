from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from requests import put, get
from db_commands import regions
import argparse

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('gene')

class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}


class Regions(Resource):

    def get(self):
        args = parser.parse_args()
        r = regions()
        result = r.get_regions_by_gene(args.gene)
        return result

class Projects(Resource):
    def get(self):
        pass

class Panels(Resource):
    def get(self):
        pass

api.add_resource(HelloWorld, '/hello')
api.add_resource(Regions, '/regions')

if __name__ == '__main__':
    app.run(debug=True)
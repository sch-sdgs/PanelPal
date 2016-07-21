from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from requests import put, get
from db_commands import regions
import argparse

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()

class RegionsGene(Resource):

    def get(self,gene):
        r = regions()
        result = r.get_regions_by_gene(gene)
        return result

class RegionsTx(Resource):

    def get(self, tx):
        r = regions()
        result = r.get_regions_by_tx(tx)
        return result

class Projects(Resource):
    def get(self):
        pass

class Panels(Resource):
    def get(self):
        pass

class Helpers():
    def conver_to_bed(self,json):
        pass

api.add_resource(RegionsGene, '/regions/gene/<string:gene>')
api.add_resource(RegionsTx, '/regions/tx/<string:tx>')

if __name__ == '__main__':
    app.run(debug=True)
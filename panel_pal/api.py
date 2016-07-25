from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from requests import put, get
from db_commands import regions
import argparse

app = Flask(__name__)
app.config['BUNDLE_ERRORS'] = True
api = Api(app)


parser = reqparse.RequestParser()

class RegionsGene(Resource):

    def get(self,gene):
        r = regions()
        result = r.get_regions_by_gene(gene)
        h = Helpers()
        return h.convert_to_bed(result)

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
    def convert_to_bed(self,json_data):
        lines = []
        for i in json_data:
            if "exons" not in i:
                for j in json_data[i]:
                    if "exons" in json_data[i][j]:
                        for k in json_data[i][j]["exons"]:
                            start = k["start"]
                            end = k["end"]
                            number = k["number"]
                            out = [start,end,number]
                            lines.append("\t".join(str(x) for x in out))

        return "\n".join(lines)


api.add_resource(RegionsGene, '/regions/gene/<string:gene>')
api.add_resource(RegionsTx, '/regions/tx/<string:tx>')

if __name__ == '__main__':
    app.run(debug=True)
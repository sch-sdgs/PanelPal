from flask import Flask, Response, jsonify
from flask_restful import Resource, Api,reqparse,fields, marshal
from requests import put, get, request
from db_commands import *
import json
import argparse
import sqlite3
from flask_restful_swagger import swagger

app = Flask(__name__)
app.config['BUNDLE_ERRORS'] = True
api =swagger.docs(Api(app),apiVersion='0.1')



@api.representation('text/bed')
def output_bed(data, headers=None):
    h = Helpers()
    resp = app.make_response(str(h.convert_to_bed(data))+"\n")
    resp.headers.extend(headers or {})
    return resp

parser = reqparse.RequestParser()

# @app.errorhandler(404)
# def not_found(error=None):
#     message = {
#             'status': 404,
#             'message': 'Not Found: ' + request.url,
#     }
#     resp = jsonify(message)
#     resp.status_code = 404
#
#     return resp

class RegionsGene(Resource):
    @swagger.operation(
        notes='some really good notes',
        responseClass='x',
        nickname='upload',
        parameters=[
            {
                "name": "body",
                "description": "blueprint object that needs to be added. YAML.",
                "required": True,
                "allowMultiple": False,
                "dataType": 'x',
                "paramType": "body"
            }
        ],
        responseMessages=[
            {
                "code": 201,
                "message": "Created. The URL of the created blueprint should be in the Location header"
            },
            {
                "code": 405,
                "message": "Invalid input"
            }
        ]
    )

    def get(self,gene):
        r = regions()
        result = r.get_regions_by_gene(gene)
        resp = output_bed(result)
        resp.status_code = 200
        return resp

class RegionsTx(Resource):

    def get(self, tx):
        r = regions()
        result = r.get_regions_by_tx(tx)
        return result

class Projects(Resource):
    def get(self):
        pass

class Panels(Resource):
    @swagger.operation(
        notes='some really good notes',
        responseClass='x',
        nickname='upload',
        parameters=[
            {
                "name": "body",
                "description": "blueprint object that needs to be added. YAML.",
                "required": True,
                "allowMultiple": False,
                "dataType": 'x',
                "paramType": "body"
            }
        ],
        responseMessages=[
            {
                "code": 201,
                "message": "Created. The URL of the created blueprint should be in the Location header"
            },
            {
                "code": 405,
                "message": "Invalid input"
            }
        ]
    )


    def get(self,id):
        conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
        conn_ref = sqlite3.connect('../panel_pal/resources/refflat.db')
        result = get_panel(conn_panelpal,conn_ref,id)
        return result

class Helpers():
    def convert_to_bed(self,json_data):
        lines = []
        print json_data
        for i in json_data:
            if "exons" not in i:
                for j in json_data[i]:
                    chrom = json_data[i]["chrom"]
                    if "exons" in json_data[i][j]:
                        for k in json_data[i][j]["exons"]:
                            start = k["start"]
                            end = k["end"]
                            number = k["number"]
                            out = [chrom,start,end,"ex"+str(number)+"_"+i+"_"+j]
                            lines.append("\t".join(str(x) for x in out))

        return "\n".join(lines)


api.add_resource(RegionsGene, '/api/regions/gene/<string:gene>')
api.add_resource(RegionsTx, '/api/regions/tx/<string:tx>')
api.add_resource(Panels, '/api/regions/panel/<string:id>')


if __name__ == '__main__':
    app.run(debug=True,host= '10.182.131.21',port=5001)
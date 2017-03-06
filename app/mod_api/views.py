from app.panel_pal import app,s
from queries import get_panel_api, get_exonic_api, get_vpanel_api, get_preftx_api
from flask import request, Blueprint
from flask_restful_swagger import swagger
from flask_restful import Resource, Api, reqparse, fields
import json

api_blueprint = Blueprint('api_blueprint', __name__)

api = swagger.docs(Api(api_blueprint), apiVersion='0.0', api_spec_url='/spec', description="PanelPal API")

class ChrSorter():
    def __init__(self):
        pass

    @staticmethod
    def lt_helper(a):
        """
        helper to sort chromosmes properly

        :param a: sort object
        :return:
        """
        try:
            return int(a)
        except ValueError:
            if a == "X":
                return 24
            elif a == "Y":
                return 25
            elif a == "MT" or a == "M":
                return 26
            else:
                return 27

    @staticmethod
    def __lt__(a, b):
        """
        run the chromosome sort helper

        :param a:
        :param b:
        :return: proper sorted chromosomes
        """
        return cmp(ChrSorter.lt_helper(a), ChrSorter.lt_helper(b))




region_fields = {
    'start': fields.Integer,
    'end': fields.Integer,
    'chrom': fields.String,
    'annotation': fields.String
}

details_fields = {
    'version': fields.Integer,
    'panel': fields.String
}

panel_fields = {
    'details': fields.Nested(details_fields),
    'regions': fields.List(fields.Nested(region_fields))

}


# todo - need to add extensions from db here
def region_result_to_json(data, extension=0):
    args = request.args
    if 'extension' in args:
        extension = int(args["extension"])
    else:
        extension = 0
    result = dict()
    result['details'] = dict()
    result['regions'] = list()
    regions = dict()
    for i in data:
        region = dict()
        if i.Versions.extension_5 is not None:
            region['start'] = i.Regions.start - extension + i.Versions.extension_5
        else:
            region['start'] = i.Regions.start - extension
        if i.Versions.extension_3 is not None:
            region['end'] = i.Regions.end + extension + i.Versions.extension_3
        else:
            region['end'] = i.Regions.end + extension
        region["annotation"] = "ex" + str(i.Exons.number) + "_" + i.Genes.name + "_" + str(i.Tx.accession)
        if i.Regions.chrom.replace('chr', '') not in regions:
            regions[i.Regions.chrom.replace('chr', '')] = list()
        regions[i.Regions.chrom.replace('chr', '')].append(region)

    for i in sorted(regions, cmp=ChrSorter.__lt__):

        for details in regions[i]:
            region = dict()
            region["chrom"] = "chr" + str(i)
            region["start"] = details["start"]
            region["end"] = details["end"]
            region["annotation"] = details["annotation"]
            result['regions'].append(region)

    return result

def prefttx_result_to_json(data):
    result = {}
    preftxs = []
    result["details"] = {}
    for i in data:
        preftxs.append(i.accession)
    result["preftx"] = preftxs
    return result


@api.representation('application/json')
def output_json(data, code, headers=None):
    # todo marshal breaks swagger here - swaggermodels?
    resp = app.make_response(json.dumps(data))
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

class APIPanels(Resource):
    @swagger.operation(
        notes='Gets a JSON of all regions in the panel - this is equivalent to the broad panel',
        responseClass='x',
        nickname='broad',
        parameters=[
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
    def get(self, name, version):
        result = get_panel_api(s, name, version)
        result_json = region_result_to_json(result.result)
        result_json["details"]["panel"] = name
        result_json["details"]["version"] = int(result.current_version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp


class APIVirtualPanels(Resource):
    @swagger.operation(
        notes='Gets a JSON of regions in a virtual panel - this is equivalent to the small panel',
        responseClass='x',
        nickname='small',
        parameters=[
            {
                "name": "extension",
                "paramType": "query",
                "required": False,
                "allowMultiple": False,
                "dataType": "integer"
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
    def get(self, name, version):
        result = get_vpanel_api(s, name, version)
        result_json = region_result_to_json(result.result)
        result_json["details"]["panel"] = name
        result_json["details"]["version"] = int(result.current_version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp

class APIPreferredTx(Resource):
    @swagger.operation(
        notes='Gets a JSON of all preftx',
        responseClass='x',
        nickname='preftx',
        parameters=[
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
    def get(self, name, version):
        result = get_preftx_api(s, name, version)
        #result_json = region_result_to_json(result.panel)
        result_json = prefttx_result_to_json(result.result)
        result_json["details"]["project"] = name
        result_json["details"]["version"] = int(result.current_version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp

# class Exonic(Resource):
#     @swagger.operation(
#         notes='Gets a JSON of regions in a virtual panel and adjusts for "exnoic" - equivalent to the exon file',
#         responseClass='x',
#         nickname='small',
#         parameters=[
#         ],
#         responseMessages=[
#             {
#                 "code": 201,
#                 "message": "Created. The URL of the created blueprint should be in the Location header"
#             },
#             {
#                 "code": 405,
#                 "message": "Invalid input"
#             }
#         ]
#     )
#     def get(self, name, version):
#         result = get_exonic_api(s, name, version)
#         result_json = region_result_to_json(result.panel,scope="exonic")
#         result_json["details"]["panel"] = name
#         result_json["details"]["version"] = int(result.current_version)
#         resp = output_json(result_json, 200)
#         resp.headers['content-type'] = 'application/json'
#         return resp


api.add_resource(APIPanels, '/panel/<string:name>/<string:version>', )
api.add_resource(APIVirtualPanels, '/virtualpanel/<string:name>/<string:version>', )
api.add_resource(APIPreferredTx, '/preftx/<string:name>/<string:version>', )
# api.add_resource(Exonic, '/api/exonic/<string:name>/<string:version>', )
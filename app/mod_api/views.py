from app.panel_pal import app, s
from queries import get_intronic_api, get_preftx_api, get_gene_api
from app.mod_panels.queries import get_regions_by_panelid, get_regions_by_vpanelid, get_panel_id_by_name, get_vpanel_id_by_name, get_current_version_vp, get_current_version
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
        helper to sort chromosomes properly

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

def region_result_to_json(data):
    result = dict()
    result['details'] = dict()
    result['regions'] = list()
    regions = dict()
    for i in data:
        region = dict()
        region['start'] = i.region_start
        region['end'] = i.region_end
        region["annotation"] = i.gene_name + ":" + i.name
        if i.chrom.replace('chr', '') not in regions:
            regions[i.chrom.replace('chr', '')] = list()
        regions[i.chrom.replace('chr', '')].append(region)

    for i in sorted(regions, cmp=ChrSorter.__lt__):
        for details in regions[i]:
            region = dict()
            region["chrom"] = "chr" + str(i)
            region["start"] = details["start"]
            region["end"] = details["end"]
            region["annotation"] = details["annotation"]
            result['regions'].append(region)

    return result

def gene_result_to_json(data):
    result = dict()
    result['details'] = dict()
    result['regions'] = list()
    regions = dict()
    for i in data:
        region = dict()
        region['start'] = i.region_start
        region['end'] = i.region_end
        region["annotation"] = i.annotation
        if i.chrom.replace('chr', '') not in regions:
            regions[i.chrom.replace('chr', '')] = list()
        regions[i.chrom.replace('chr', '')].append(region)

    for i in sorted(regions, cmp=ChrSorter.__lt__):
        for details in regions[i]:
            region = dict()
            region["chrom"] = "chr" + str(i)
            region["start"] = details["start"]
            region["end"] = details["end"]
            region["annotation"] = details["annotation"]
            result['regions'].append(region)

    return result

def intronic_result_to_json(data):
    result = dict()
    result["details"] = dict()
    result["regions"] = list()
    regions = dict()

    for i in data:
        print(i)
        region = dict()
        region["start"] = i.start
        region["end"] = i.end
        region["annotation"] = ""
        if i.chrom.replace('chr', '') not in regions:
            regions[i.chrom.replace('chr', '')] = list()
        regions[i.chrom.replace('chr', '')].append(region)

    for i in sorted(regions, cmp=ChrSorter.__lt__):
        for details in regions[i]:
            region = dict()
            region["chrom"] = "chr" + str(i)
            region["start"] = details["start"]
            region["end"] = details["end"]
            region["annotation"] = details["annotation"]
            print(region)
            result['regions'].append(region)

    return result

def prefttx_result_to_json(data):
    result = {}
    preftxs = []
    result["details"] = {}
    for i in data:
        preftxs.append((i.gene, i.accession))
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
        panel_id = get_panel_id_by_name(s, name)
        if version == "current":
            version = get_current_version(s, panel_id)
        result = get_regions_by_panelid(s, panel_id, version, 25)
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
        extension = request.args.get("extension")
        vpanel_id = get_vpanel_id_by_name(s, name)
        if not extension:
            print(extension)
            extension = 0
        if version == "current":
            version = get_current_version_vp(s, vpanel_id)
        result = get_regions_by_vpanelid(s, vpanel_id, version, extension)
        result_json = region_result_to_json(result)
        result_json["details"]["panel"] = name
        result_json["details"]["version"] = float(version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp


class APIIntronic(Resource):
    @swagger.operation(
        notes='Gets a JSON of the intronic portion of the bed virtual panel (i.e. +/- 6bp to +/- 25 bp)',
        responseClass='x',
        nickname='intronic',
        parameters=[],
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
        result = get_intronic_api(s, name, version)
        result_json = intronic_result_to_json(result.result)
        result_json['details']['panel'] = name
        result_json['details']['version'] = result.current_version
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp

class APIGene(Resource):
    @swagger.operation(
        notes='Gets a JSON of the intronic portion of the bed virtual panel (i.e. +/- 6bp to +/- 25 bp)',
        responseClass='x',
        nickname='intronic',
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
        extension = request.args.get("extension")
        if not extension:
            extension = 1000
        result = get_gene_api(s, name, version, extension)
        result_json = gene_result_to_json(result.result)
        result_json['details']['panel'] = name
        result_json['details']['version'] = result.current_version
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
        # result_json = region_result_to_json(result.panel)
        result_json = prefttx_result_to_json(result.result)
        result_json["details"]["project"] = name
        result_json["details"]["version"] = int(result.current_version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp


api.add_resource(APIPanels, '/panel/<string:name>/<string:version>', )
api.add_resource(APIVirtualPanels, '/virtualpanel/<string:name>/<string:version>', )
api.add_resource(APIIntronic, '/intronic/<string:name>/<string:version>/', )
api.add_resource(APIGene, '/filled/<string:name>/<string:version>', )
api.add_resource(APIPreferredTx, '/preftx/<string:name>/<string:version>', )

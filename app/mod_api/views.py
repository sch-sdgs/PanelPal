from app.panel_pal import app, s
from queries import get_intronic_api, get_preftx_api, get_gene_api, get_project_from_vp, get_vpanel_id_from_testcode
from app.mod_panels.queries import get_regions_by_panelid, get_regions_by_vpanelid, get_panel_id_by_name, \
    get_vpanel_id_by_name, get_current_version_vp, get_current_version, get_panel_by_vp_name, get_panel_details_by_id, \
    get_panel_by_vp_id, get_vpanel_name_by_id
from app.mod_projects.queries import get_project_id_by_name, get_current_preftx_version, get_preftx_id_by_project_id
from flask import request, Blueprint
from flask_restful_swagger import swagger
from flask_restful import Resource, Api, reqparse, fields
import json

api_blueprint = Blueprint('api_blueprint', __name__)
api = swagger.docs(Api(api_blueprint, catch_all_404s=True), apiVersion='0.0', api_spec_url='/spec',
                   description="PanelPal API")

responses = [
    {
        "code": 200,
        "message": "Created. The URL of the created blueprint should be in the Location header"
    },
    {
        "code": 400,
        "message": "Invalid input"
    },
    {
        "code": 422,
        "message": "Object not found"
    }
]


class ChrSorter:
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
        preftxs.append((i.name, i.accession))
    result["preftx"] = preftxs
    return result


@api.representation('application/json')
def output_json(data, code, headers=None):
    # todo marshal breaks swagger here - swaggermodels?
    resp = app.make_response(json.dumps(data))
    resp.headers.extend(headers or {})
    return resp


parser = reqparse.RequestParser()


class APIPanels(Resource):
    @swagger.operation(
        notes='Gets a JSON of all regions in the panel - this is equivalent to the broad panel',
        responseClass='x',
        nickname='broad',
        parameters=[
            {
                "name": "name",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The panel name to be used to fetch the regions"
            },
            {
                "name": "version",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The version to be retrieved, this can be 'current' if the specific version is not known"
            }
        ],
        responseMessages=responses
    )
    def get(self, name, version):
        panel_id = get_panel_id_by_name(s, name)
        if not panel_id:
            return ObjectNotFoundError(name, 'panels')
        current_version = get_current_version(s, panel_id)
        if version == "current":
            version = current_version
        elif int(version) > current_version:
            message = "Version {} for {} either does not exist or has not been made live yet.".format(version, name)
            return IncorrectParametersError(message)
        if version == 0:
            return PanelNotLiveError(name)
        result = get_regions_by_panelid(s, panel_id, version, 25)
        result_json = region_result_to_json(result)
        result_json["details"]["panel"] = name
        result_json["details"]["version"] = int(version)
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
                "name": "name",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The name of the virtual panel to be used to retrieve the regions"
            },
            {
                "name": "version",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The version to be retrieved, this can be 'current' if the specific version is not known"
            },
            {
                "name": "extension",
                "paramType": "query",
                "required": False,
                "allowMultiple": False,
                "dataType": "integer",
                "description": "The extension to be added to each region in the panel. If not provided, the default is 0."
            }
        ],
        responseMessages=responses
    )
    def get(self, name, version):
        extension = request.args.get("extension")
        vpanel_id = get_vpanel_id_by_name(s, name)
        if not vpanel_id:
            return ObjectNotFoundError(name, 'virtual panels')
        current_version = get_current_version_vp(s, vpanel_id)
        if not extension:
            print(extension)
            extension = 0
        if version == "current":
            version = current_version
        elif float(version) > current_version:
            message = "Version {} for {} either does not exist or has not been made live yet.".format(version, name)
            return IncorrectParametersError(message)
        if int(current_version) == current_version:#if the version number ends in .0 the panel has never been made live
            return PanelNotLiveError(name)
        result = get_regions_by_vpanelid(s, vpanel_id, version, extension)
        result_json = region_result_to_json(result)
        result_json["details"]["panel"] = name
        result_json["details"]["version"] = float(version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp


class APITestCode(Resource):
    @swagger.operation(
        notes='Gets a JSON of regions in a virtual panel using the test code in StarLIMS - this is equivalent to the small panel',
        responseClass='x',
        nickname='small',
        parameters=[
            {
                "name": "test_code",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The test code in StarLIMS for the virtual panel. This also determines the version"
            },
            {
                "name": "extension",
                "paramType": "query",
                "required": False,
                "allowMultiple": False,
                "dataType": "integer",
                "description": "The extension to be added to each region in the panel. If not provided, the default is 0."
            }
        ],
        responseMessages=responses
    )
    def get(self, test_code):
        extension = request.args.get("extension")
        vpanel_id, version = get_vpanel_id_from_testcode(s, test_code)
        if not vpanel_id:
            return ObjectNotFoundError(test_code, 'test codes')
        current_version = get_current_version_vp(s, vpanel_id)
        if not extension:
            extension = 0
        result = get_regions_by_vpanelid(s, vpanel_id, current_version, extension)
        result_json = region_result_to_json(result)
        result_json["details"]["panel"] = get_vpanel_name_by_id(s, vpanel_id)
        result_json["details"]["version"] = float(version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp


class APIIntronic(Resource):
    @swagger.operation(
        notes='Gets a JSON of the intronic portion of the bed virtual panel (i.e. +/- 6bp to +/- 25 bp)',
        responseClass='x',
        nickname='intronic',
        parameters=[
            {
                "name": "name",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The name of the virtual panel to be used to retrieve the regions"
            },
            {
                "name": "version",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The version to be retrieved, this can be 'current' if the specific version is not known"
            }
        ],
        responseMessages=responses
    )
    def get(self, name, version):
        vp_id = get_vpanel_id_by_name(s, name)
        print(vp_id)
        if not vp_id:
            return ObjectNotFoundError(name, 'virtual panels')
        current_version = get_current_version_vp(s, vp_id)
        if version == "current":
            version = current_version
        elif float(version) > current_version:
            message = "Version {} for {} either does not exist or has not been made live yet.".format(version, name)
            return IncorrectParametersError(message)
        if int(current_version) == current_version:
            return PanelNotLiveError(name)
        result = get_intronic_api(s, vp_id, str(version))
        result_json = intronic_result_to_json(result.result)
        result_json['details']['panel'] = name
        result_json['details']['version'] = result.current_version
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp

class APIIntronicFromTestCode(Resource):
    @swagger.operation(
        notes='Gets a JSON of the intronic portion of the bed virtual panel (i.e. +/- 6bp to +/- 25 bp)',
        responseClass='x',
        nickname='intronic',
        parameters=[
            {
                "name": "test_code",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The test code "
            }
        ],
        responseMessages=responses
    )
    def get(self, test_code):
        vp_id, version = get_vpanel_id_from_testcode(s, test_code)
        if not vp_id:
            return ObjectNotFoundError(test_code, 'test codes')
        result = get_intronic_api(s, vp_id, str(version))
        result_json = intronic_result_to_json(result.result)
        result_json['details']['panel'] = get_vpanel_name_by_id(s, vp_id)
        result_json['details']['version'] = result.current_version
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp



class APIGene(Resource):
    @swagger.operation(
        notes='Gets a JSON of the gene regions for a given panel. This method takes the highest and lowest exon coordinates for all transcripts as the start and end for each region. An extension is also added to each region',
        responseClass='x',
        nickname='intronic',
        parameters=[
            {
                "name": "name",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The name of the panel to be used to retrieve the regions"
            },
            {
                "name": "version",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The version to be retrieved, this can be 'current' if the specific version is not known"
            },
            {
                "name": "extension",
                "paramType": "query",
                "required": False,
                "allowMultiple": False,
                "dataType": "integer",
                "description": "The extension to be added to the regions. The default value is 1000"
            }
        ],
        responseMessages=responses
    )
    def get(self, name, version):
        extension = request.args.get("extension")
        if not extension:
            extension = 1000
        panel_id = get_panel_id_by_name(s, name)
        if not panel_id:
            return ObjectNotFoundError(name, 'panels')
        if version == "current":
            version = get_current_version(s, panel_id)
        if version == 0:
            return PanelNotLiveError(name)
        result = get_gene_api(s, panel_id, version, extension)
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
            {
                "name": "project_name",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The name of the project to be used to retrieve the preferred tx"
            },
            {
                "name": "version",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The preftx version to be retrieved, this can be 'current' if the specific version is not known"
            }
        ],
        responseMessages=responses
    )
    def get(self, project_name, version):
        project_id = get_project_id_by_name(s, project_name)
        if not project_id:
            return ObjectNotFoundError(project_name, 'projects')
        preftx_id = get_preftx_id_by_project_id(s, project_id)
        current_version = get_current_preftx_version(s, preftx_id)
        if version == "current":
            version = current_version
        elif int(version) > current_version:
            message = "Version {} for {} either does not exist or has not been made live yet.".format(version,
                                                                                                      "preferred tx for " + project_name)
            return IncorrectParametersError(message)
        if version == 0:
            return PanelNotLiveError("Preferred transcripts for " + project_name)
        result = get_preftx_api(s, project_id, version)
        result_json = prefttx_result_to_json(result.result)
        result_json["details"]["project"] = project_name
        result_json["details"]["version"] = int(result.current_version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp


def get_panel(vp_id, version, message):
    """

    :param vp_id:
    :param version:
    :param message:
    :return:
    """
    panel_id = get_panel_by_vp_id(s, vp_id)
    panel_name = get_panel_details_by_id(s, panel_id).name
    current_version = int(get_current_version_vp(s, vp_id) // 1)
    if version == "current":
        panel_version = current_version
    elif int(version.split('.')[0]) > current_version:
        return IncorrectParametersError(message)
    else:
        panel_version = version.split('.')[0]
    result = get_regions_by_panelid(s, panel_id, panel_version, 25)
    result_json = region_result_to_json(result)
    result_json["details"]["panel"] = panel_name
    result_json["details"]["version"] = int(panel_version)
    resp = output_json(result_json, 200)
    resp.headers['content-type'] = 'application/json'
    return resp


class APIPanelFromVPanel(Resource):
    @swagger.operation(
        notes='Gets a JSON of all regions in the panel using the virtual panel name - this is equivalent to the broad panel',
        responseClass='x',
        nickname='broad',
        parameters=[
            {
                "name": "name",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The name of the panel to be used to retrieve the regions"
            },
            {
                "name": "version",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The version of the VIRTUAL PANEL to be retrieved, this can be 'current' if the specific version is not known"
            }
        ],
        responseMessages=responses
    )
    def get(self, name, version):
        vpanel_id = get_vpanel_id_by_name(s, name)
        if not vpanel_id:
            return ObjectNotFoundError(name, "virtual panels")
        message = "Version {} for {} either does not exist or has not been made live yet.".format(version, name)
        resp = get_panel(vpanel_id, version, message)
        return resp


class APIPanelFromTestCode(Resource):
    @swagger.operation(
        notes='Gets a JSON of all regions in the panel using the virtual panel name - this is equivalent to the broad panel',
        responseClass='x',
        nickname='broad',
        parameters=[
            {
                "name": "test_code",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "integer",
                "description": "The test code from StarLIMS to be used to retrieve the virtual panel. This also determines the version."
            }
        ],
        responseMessages=responses
    )
    def get(self, test_code):
        vpanel_id, version = get_vpanel_id_from_testcode(s, test_code)
        if not vpanel_id:
            return ObjectNotFoundError(test_code, "test codes")
        message = "Version {} for {} either does not exist or has not been made live yet.".format(version,
                                                                                                  get_vpanel_name_by_id(
                                                                                                      s, vpanel_id))
        resp = get_panel(vpanel_id, str(version), message)
        return resp


def get_filled(vpanel_id, version, extension, message):
    """

    :param vpanel_id:
    :param version:
    :param extension:
    :param message:
    :return:
    """
    panel_id = get_panel_by_vp_id(s, vpanel_id)
    panel_name = get_panel_details_by_id(s, panel_id).name
    current_version = int(get_current_version_vp(s, vpanel_id) // 1)
    if version == "current":
        panel_version = current_version
    elif int(version.split('.')[0]) > current_version:
        return IncorrectParametersError(message)
    else:
        panel_version = version.split('.')[0]

    if not extension:
        extension = 1000
    result = get_gene_api(s, panel_id, panel_version, extension)
    result_json = gene_result_to_json(result.result)
    result_json["details"]["panel"] = panel_name
    result_json["details"]["version"] = int(panel_version)
    resp = output_json(result_json, 200)
    resp.headers['content-type'] = 'application/json'
    return resp


class APIFilledFromVPanel(Resource):
    @swagger.operation(
        notes='Gets a JSON of all gene regions in the panel using the virtual panel name',
        responseClass='x',
        nickname='broad',
        parameters=[
            {
                "name": "name",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The name of the panel to be used to retrieve the regions"
            },
            {
                "name": "version",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The version of the VIRTUAL PANEL to be retrieved, this can be 'current' if the specific version is not known"
            },
            {
                "name": "extension",
                "paramType": "query",
                "required": False,
                "allowMultiple": False,
                "dataType": "integer",
                "description": "The extension to be added to each region in the panel. If not provided, the default is 0."
            }

        ],
        responseMessages=responses
    )
    def get(self, name, version):
        vpanel_id = get_vpanel_id_by_name(s, name)
        if not vpanel_id:
            return ObjectNotFoundError(name, 'virtual panels')
        message = "Version {} for {} either does not exist or has not been made live yet.".format(version, name)
        resp = get_filled(vpanel_id, version, request.args.get('extension'), message)
        return resp


class APIFilledFromTestCode(Resource):
    @swagger.operation(
        notes='Gets a JSON of all gene regions in the panel using the virtual panel name',
        responseClass='x',
        nickname='broad',
        parameters=[
            {
                "name": "test_code",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The Test Code set in StarLIMS for virtual panel. This also determines the version"
            },
            {
                "name": "extension",
                "paramType": "query",
                "required": False,
                "allowMultiple": False,
                "dataType": "integer",
                "description": "The extension to be added to each region in the panel. If not provided, the default is 0."
            }

        ],
        responseMessages=responses
    )
    def get(self, test_code):
        vpanel_id, version = get_vpanel_id_from_testcode(s, test_code)
        if not vpanel_id:
            return ObjectNotFoundError(test_code, 'test codes')
        message = "Version {} for {} either does not exist or has not been made live yet.".format(version,
                                                                                                  get_vpanel_name_by_id(
                                                                                                      s, vpanel_id))
        resp = get_filled(vpanel_id, str(version), request.args.get('extension'), message)
        return resp


def get_preftx(vp_id):
    """

    :param vp_id:
    :return:
    """
    project = get_project_from_vp(s, vp_id)
    project_name = project.name
    project_id = project.id
    preftx_id = get_preftx_id_by_project_id(s, project_id)
    version = get_current_preftx_version(s, preftx_id)
    result = get_preftx_api(s, project_id, version)
    result_json = prefttx_result_to_json(result.result)
    result_json["details"]["project"] = project_name
    result_json["details"]["version"] = int(result.current_version)
    resp = output_json(result_json, 200)
    resp.headers['content-type'] = 'application/json'
    return resp


class APIPrefTxFromVPanel(Resource):
    @swagger.operation(
        notes='Gets a JSON of preferred tx using the virtual panel name - only the current version can be retrieved',
        responseClass='x',
        nickname='broad',
        parameters=[
            {
                "name": "vpanel_name",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The name of the virtual panel to be used to get the preferred tx"
            }
        ],
        responseMessages=responses
    )
    def get(self, vpanel_name):
        vp_id = get_vpanel_id_by_name(s, vpanel_name)
        if not vp_id:
            return ObjectNotFoundError(vpanel_name, 'virtual panels')
        resp = get_preftx(vp_id)
        return resp


class APIPrefTxFromTestCode(Resource):
    @swagger.operation(
        notes='Gets a JSON of preferred tx using the virtual panel test code - only the current version can be retrieved',
        responseClass='x',
        nickname='broad',
        parameters=[
            {
                "name": "test_code",
                "paramType": "path",
                "required": True,
                "allowMultiple": False,
                "dataType": "string",
                "description": "The test code from StarLIMS for the required virtual panel"
            }
        ],
        responseMessages=responses
    )
    def get(self, test_code):
        vp_id, version = get_vpanel_id_from_testcode(s, test_code)
        if not vp_id:
            return ObjectNotFoundError(test_code, 'test codes')
        resp = get_preftx(vp_id)
        return resp


class APITest(Resource):
    @swagger.operation(
        notes='Returns "pass" so the API can be confirmed to be active',
        responseClass='x',
        nickname='test',
        parameters=[],
        responseMessage=[
            {
                "code": 200,
                "message": "Created. The URL of the created blueprint should be in the Location header"
            },
            {
                "code": 405,
                "message": "Invalid input"
            }
        ]
    )
    def get(self):
        return "pass"


def ObjectNotFoundError(panel, table):
    """
    Method to return an error response if the panel given doesn't exist

    :param panel: name or ID given for panel
    :param table: the database table being queried (e.g. panels/projects etc)
    :return:
    """
    response = {'message': "{} was not found in {}".format(panel, table)}
    result = output_json(response, 422)
    result.status_code = 422
    result.headers['content-type'] = 'application/json'
    return result


def IncorrectParametersError(message):
    """
    Method to return an error response if incorrect arguments have been given

    :param message: message to be returned in response
    :return:
    """
    response = {'message': message}
    result = output_json(response, 400)
    result.status_code = 400
    result.headers['content-type'] = 'application/json'
    return result

def PanelNotLiveError(name):
    """
    Method to return an error response if incorrect arguments have been given

    :param name: The name of the panel
    :return:
    """
    message = "{} does not have a live version so cannot be retrieved through the API".format(name)
    response = {'message': message}
    result = output_json(response, 400)
    result.status_code = 400
    result.headers['content-type'] = 'application/json'
    return result


api.add_resource(APITest, '/test')

api.add_resource(APIPanels, '/panel/name/<string:name>/<string:version>')
api.add_resource(APIPanelFromVPanel, '/panel/virtual/<string:vpanel_name>/<string:version>', )
api.add_resource(APIPanelFromTestCode, '/panel/testcode/<int:test_code>')

api.add_resource(APIVirtualPanels, '/virtualpanel/name/<string:name>/<string:version>')
api.add_resource(APITestCode, '/virtualpanel/testcode/<int:test_code>')

api.add_resource(APIIntronic, '/intronic/name/<string:name>/<string:version>/')
api.add_resource(APIIntronicFromTestCode, '/intronic/testcode/<int:test_code>')

api.add_resource(APIGene, '/filled/name/<string:name>/<string:version>')
api.add_resource(APIFilledFromVPanel, '/filled/virtual/<string:vpanel_name>/<string:version>', )
api.add_resource(APIFilledFromTestCode, '/filled/testcode/<int:test_code>')

api.add_resource(APIPreferredTx, '/preftx/name/<string:project_name>/<string:version>', )
api.add_resource(APIPrefTxFromVPanel, '/preftx/virtual/<string:vpanel_name>', )
api.add_resource(APIPrefTxFromTestCode, '/preftx/testcode/<int:test_code>')
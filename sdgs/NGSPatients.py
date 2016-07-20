from protocols.SDGSProtocols import *
import xml.etree.ElementTree as ET
import requests
from enum import Enum

class AnalysisStatus(Enum):
    fail = 0
    pending = 1
    running = 2
    complete = 3

def get_records():
    """
    runs web request to retrieve all patients who are set to NGS pipeline or NGS reanalysis and logged or need prep
    reads in xml and only returns results elements
    :return rows: An array of xml elements that contain a patient record to be submitted to the server
    """

    url = "http://10.182.155.37/StarLimsWeb.asmx/NGSAnalysis"
    headers = {'content-type': 'text/xml'}
    body = """"<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
              <soap:Body>
                <NGSAnalysis xmlns="http://10.182.155.37.sch.nhs.uk/StarLimsWeb.asmx" />
              </soap:Body>
            </soap:Envelope>"""

    response = requests.post(url, data = body, headers = headers)

    tree = ET.fromstring(response.text)
    rows = list(tree.iter('results'))

    return rows

def create_analysis(element):
    analysis = Analysis()
    analysis.smallBed = element.findtext('PANELBEDFILE')
    analysis.polylist = element.findtext('POLYMORPHISMLISTFILE')
    analysis.status = AnalysisStatus.pending.value

    return analysis


def initial_analysis_patient(element):
    """
    Create a new patient/specimen/sequencingrun as required and send to arvados
    :param element: xml element containing results from SQL query
    :return NGSPatient: NGSPatient model
    """

    p = NGSPatient()
    # todo: add query to check if patient has already been processed and is pending/running/complete: if patient already exists, check status and update if necessary
    gender = element.findtext('GENDER')
    if gender is 'Male':
        p.sex = 'M'
    elif gender is 'Female':
        p.sex = 'F'
    else:
        p.sex = 'U'

    p.id = element.findtext('FOLDERNO')
    # todo: add population of version control

    analysis = create_analysis(element)

    run = SequencingRun()
    run.worklistNumber = element.findtext('RunNumber')
    run.runName = element.findtext('MISEQ_RUN_NAME')
    run.runPosition = element.findtext('POSITION_IN_RUN')
    run.captureMethod = element.findtext('CAPTUREMETHOD')
    run.broadBed = element.findtext('BED')
    run.analyses = [analysis]

    s = Specimen()
    s.id = element.findtext('CONTAINERID')
    s.sequencingRuns = [run]
    p.specimens = [s]

    try:
        p.validate(p.toJsonDict())
    except False:
        print "error: the model did not validate (" + element.findtext('FOLDERNO') + ")"
    return p



def reanalysis_patient(element):
    """
    Creates the analysis model and links to existing patient, specimen and sequencing run
    :param element: xml element containing results from SQL query
    :return patient: NGSPatient model
    """
    p = NGSPatient()
    # todo: add query to retrieve patient from arvados

    '''create a new analysis for this patient and add to sequencing runs'''
    analysis = create_analysis(element)



    return p

def main():

    results = get_records()
    for record in results:
        container = record.find('CONTAINERID')
        status = record.find('STAGE')
        print status.text
        if container is not None and status.text == 'NGS Pipeline':
            patient = initial_analysis_patient(record)
            print 'ok'
            print patient.toJsonDict()



        elif container is not None and status.text == 'NGS Reanalysis':
            patient = reanalysis_patient(record)
            print 'ok'
            print patient.toJsonDict()



        '''if patient status is complete, send update to StarLims to change stage to first check'''



main()

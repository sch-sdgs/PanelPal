from sqlalchemy import and_, or_, desc, text, exc
from models import *

# TODO ?not used anywhere
# def get_genes_by_projectid(s, projectid):
#     """
#     gets transcripts by project id
#
#     :param s: db session
#     :param id: project id
#     :return: sql alchemy object
#     """
#     genes = s.query(Genes, Tx, Exons, Regions, Versions, Panels, Projects). \
#         distinct(Tx.accession). \
#         group_by(Tx.accession). \
#         join(Tx). \
#         join(Exons). \
#         join(Regions). \
#         join(Versions). \
#         join(Panels). \
#         join(Projects). \
#         filter_by(id=projectid). \
#         values(Tx.id.label("txid"), \
#                Projects.name.label("projectname"), \
#                Projects.id.label("projectid"), \
#                Genes.name.label("genename"), \
#                Genes.id.label("geneid"), \
#                Tx.accession, \
#                Tx.tx_start, \
#                Tx.tx_end, \
#                Tx.strand)
#     return genes

from app.mod_projects.queries import get_project_name, get_project_id_by_name, get_user_rel_by_project_id, \
    get_projects_by_user, get_tx_by_gene_id
from app.mod_panels.queries import get_gene_id_from_name, get_virtual_panels_by_panel_id, get_current_version, \
    get_genes_by_panelid, get_project_id_by_panel_id, get_current_version_vp, get_genes_by_vpanelid, \
    get_panels_by_project_id
from flask import Blueprint
from flask import render_template, request, jsonify
from flask.ext.login import login_required
from forms import *

from app.panel_pal import s
from flask_table import Table, Col, LinkCol
from queries import *

search = Blueprint('search', __name__, template_folder='templates')

class ItemTableSearchTx(Table):
    id = Col('Transcript Accession')

class ItemTableSearchGene(Table):
    gene_name = Col('Gene')

class ItemTableSearchVPanels(Table):
    panel_name = LinkCol('Panel', 'panels.view_panel', url_kwargs=dict(id='panel_id'), attr='panel_name')
    vpanel_name = LinkCol('Virtual Panel', 'panels.view_vpanel', url_kwargs=dict(id='vpanel_id'), attr='vpanel_name')

class ItemTableSearchVPanelsTwo(Table):
    vpanel_name = LinkCol('', 'panels.view_vpanel', url_kwargs=dict(id='vpanel_id'), attr='vpanel_name')

class ItemTableSearchPanels(Table):
    panel_name = LinkCol('', 'panels.view_panel', url_kwargs=dict(id='panel_id'), attr='panel_name')

class ItemTableSearchProjects(Table):
    project_name = LinkCol('', 'panels.view_panels', url_kwargs=dict(id='project_id'), attr='project_name')

class ItemTableSearchUsers(Table):
    username = Col('')

@search.route('/autocomplete_tx', methods=['GET'])
def autocomplete_tx():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Tx).filter(Tx.accession.like("%" + value + "%")).all()
    data = [i.accession for i in result]
    return jsonify(matching_results=data)

@search.route('/autocomplete_panel', methods=['GET'])
def autocomplete_panel():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Panels).filter(Panels.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    return jsonify(matching_results=data)

@search.route('/autocomplete_vp', methods=['GET'])
def autocomplete_vp():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(VirtualPanels).filter(VirtualPanels.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    return jsonify(matching_results=data)

@search.route('/autocomplete_project', methods=['GET'])
def autocomplete_project():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Projects).filter(Projects.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    return jsonify(matching_results=data)

@search.route('/autocomplete_user', methods=['GET'])
def autocomplete_user():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Users).filter(Users.username.like("%" + value + "%")).all()
    data = [i.username for i in result]
    return jsonify(matching_results=data)

@search.route('/', methods=['GET', 'POST'])
@login_required
def search_for():
    form = Search()
    if request.method == 'GET':
        return render_template("search.html", form=form)
    else:
        type = request.form["tables"]
        term = request.form["search_term"]

        if type == "Genes":
            tx_result=[]
            gene_id = get_gene_id_from_name(s, term)
            if gene_id:
                tx = get_tx_by_gene_id(s, gene_id)

                for t in tx:
                    tx_accession = {'id':t[1]}
                    tx_result.append(tx_accession)
                table_one = ItemTableSearchTx(tx_result, classes=['table', 'table-striped'])

                vpanel_result = []
                vpanel = get_vpanel_by_gene_id(s, gene_id)
                vpanel_list = list(vpanel)

                if len(vpanel_list) > 0:
                    for vp in vpanel_list:
                        vp_id = vp[0]
                        vp_name = vp[1]
                        broad_name = get_panel_by_vpanel_id(s, vp_id)
                        for b in broad_name:
                            vpanel_info = {'vpanel_name': vp_name, 'vpanel_id': vp_id, 'panel_name': b[0], 'panel_id': b[1]}
                            vpanel_result.append(vpanel_info)
                    table_two = ItemTableSearchVPanels(vpanel_result, classes=['table', 'table-striped'])
                else:
                    panel_results=[]
                    panel = get_panel_by_gene_id(s, gene_id)
                    for p in panel:
                        p_info = {'panel_name':p[1], 'panel_id':p[0]}
                        panel_results.append(p_info)
                    table_two = ItemTableSearchPanels(panel_results, classes=['table', 'table-striped'])

                return render_template("search_results.html", genes_tx=table_one, genes_panels=table_two, term=term)

        if type == "Transcripts":
            tx_id = get_tx_id_from_name(s,term)
            if tx_id:
                gene = get_gene_from_tx(s, tx_id)
                gene_result=[]

                for g in gene:
                    gene_info = {'gene_name':g[0]}
                    gene_id = g[1]
                    gene_result.append(gene_info)
                table_one = ItemTableSearchGene(gene_result, classes=['table', 'table-striped'])

                vpanel_result = []
                vpanel = get_vpanel_by_gene_id(s, gene_id)
                vpanel_list = list(vpanel)
                if len(vpanel_list) > 0:
                    for vp in vpanel_list:
                        vp_id = vp[0]
                        vp_name = vp[1]
                        broad_name = get_panel_by_vpanel_id(s, vp_id)
                        for b in broad_name:
                            vpanel_info = {'vpanel_name': vp_name, 'vpanel_id': vp_id, 'panel_name': b[0], 'panel_id': b[1]}
                            vpanel_result.append(vpanel_info)
                    table_two = ItemTableSearchVPanels(vpanel_result, classes=['table', 'table-striped'])
                else:
                    panel_results=[]
                    panel = get_panel_by_gene_id(s, gene_id)
                    for p in panel:
                        p_info = {'panel_name':p[1], 'panel_id':p[0]}
                        panel_results.append(p_info)
                    table_two = ItemTableSearchPanels(panel_results, classes=['table', 'table-striped'])

                return render_template("search_results.html", tx_genes=table_one, tx_panels=table_two, term=term)

        if type == "Panels":
            panel = get_panel_id_by_name(s,term)
            p_list = list(panel)
            if len(p_list) > 0:
                panel_results=[]
                for p in p_list:
                    panel_id = p[0]
                    project_id = p[1]
                    panel_info = {'panel_name': term, 'panel_id': panel_id}
                    panel_results.append(panel_info)
                table_one = ItemTableSearchPanels(panel_results, classes=['table', 'table-striped'])

                project = get_project_name(s,project_id)
                project_results = [{'project_name': project, 'project_id': project_id}]
                table_two = ItemTableSearchProjects(project_results, classes=['table', 'table-striped'])

                vpanels = get_virtual_panels_by_panel_id(s, panel_id)
                vpanel_results=[]
                for vp in vpanels:
                    vpanel_info={'vpanel_name': vp[6], 'vpanel_id': vp[0]}
                    vpanel_results.append(vpanel_info)
                table_three = ItemTableSearchVPanelsTwo(vpanel_results, classes=['table', 'table-striped'])

                users = get_user_rel_by_project_id(s, project_id)
                user_results = []
                for u in users:
                    user_info = {'username': u[0]}
                    user_results.append(user_info)
                table_four = ItemTableSearchUsers(user_results, classes=['table', 'table-striped'])


                version = get_current_version(s, panel_id)
                genes = get_genes_by_panelid(s, panel_id, version)
                gene_results=[]
                for g in genes:
                    gene_info={'gene_name': g[0]}
                    gene_results.append(gene_info)
                table_five = ItemTableSearchGene(gene_results, classes=['table', 'table-striped'])

                return render_template("search_results.html", panels_panels=table_one, panels_projects=table_two, panels_vpanels=table_three, \
                                       panels_users=table_four, panels_genes=table_five, term=term)


        if type == "VPanels":
            vpanel_id = get_vpanel_id_by_name(s, term)
            v_list = list(vpanel_id)
            if len(v_list) > 0:
                for vp in v_list:
                    vpanel_id = vp[0]
                    vpanel_results=[{'vpanel_name': term, 'vpanel_id': vpanel_id}]
                table_one = ItemTableSearchVPanelsTwo(vpanel_results, classes=['table', 'table-striped'])


                panel = get_panel_by_vpanel_id(s, vpanel_id)
                for p in panel:
                    panel_id = p[1]
                    panel_results=[{'panel_name': p[0], 'panel_id': panel_id}]
                table_two = ItemTableSearchPanels(panel_results, classes=['table', 'table-striped'])

                project_id = get_project_id_by_panel_id(s, panel_id)
                project_name = get_project_name(s, project_id)
                project_results=[{'project_name': project_name, 'project_id': project_id}]
                table_three = ItemTableSearchProjects(project_results, classes=['table', 'table-striped'])

                users = get_user_rel_by_project_id(s, project_id)
                user_results = []
                for u in users:
                    user_info = {'username': u[0]}
                    user_results.append(user_info)
                table_four = ItemTableSearchUsers(user_results, classes=['table', 'table-striped'])

                version = get_current_version_vp(s, vpanel_id)
                genes = get_genes_by_vpanelid(s, panel_id, version)
                gene_results = []
                for g in genes:
                    gene_info = {'gene_name': g[0]}
                    gene_results.append(gene_info)
                table_five = ItemTableSearchGene(gene_results, classes=['table', 'table-striped'])

                return render_template("search_results.html", vpanels_vpanels=table_one, vpanels_panels=table_two, vpanels_projects=table_three, \
                                       vpanels_users=table_four, vpanels_genes=table_five, term=term)

        if type == "Projects":
            project_id = get_project_id_by_name(s, term)
            print(project_id)
            if project_id:
                project_results = [{'project_name': term, 'project_id': project_id}]
                table_one = ItemTableSearchProjects(project_results, classes=['table', 'table-striped'])

                panels = get_panels_by_project_id(s, project_id)
                panel_results = []
                for p in panels:
                    panel_id = p[4]
                    panel_name = p[2]
                    vpanels = get_virtual_panels_by_panel_id(s, panel_id)
                    vp_list = list(vpanels)
                    count=1
                    if len(vp_list)>0:
                        for vp in vp_list:
                            vp_id = vp[0]
                            vp_name = vp[6]
                            if count == 1:
                                panel_info = {'panel_name': panel_name, 'panel_id': panel_id, 'vpanel_name': vp_name, 'vpanel_id': vp_id}
                                panel_results.append(panel_info)
                                count=2
                            else:
                                panel_info = {'panel_name': '', 'panel_id': '', 'vpanel_name': vp_name, 'vpanel_id': vp_id}
                                panel_results.append(panel_info)
                    else:
                        panel_info = {'panel_name': panel_name, 'panel_id': panel_id, 'vpanel_name': '', 'vpanel_id': ''}
                        panel_results.append(panel_info)
                table_two = ItemTableSearchVPanels(panel_results, classes=['table', 'table-striped'])

                users = get_user_rel_by_project_id(s, project_id)
                user_results = []
                for u in users:
                    user_info = {'username': u[0]}
                    user_results.append(user_info)
                table_three = ItemTableSearchUsers(user_results, classes=['table', 'table-striped'])

                return render_template("search_results.html", projects_project=table_one, projects_panels=table_two, projects_users=table_three, term=term)


        if type == "Users":
            projects = get_projects_by_user(s, term)
            p_list = list(projects)
            if len(p_list) > 0:
                project_results=[]
                for p in p_list:
                    project_info = {'project_id': p[0], 'project_name': p[1]}
                    project_results.append(project_info)
                table_one = ItemTableSearchProjects(project_results, classes=['table', 'table-striped'])

                return render_template("search_results.html", users_projects=table_one, term=term)

        return render_template("search_results.html", no_results=True, term=term)
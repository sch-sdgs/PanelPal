from app.queries import *
from flask import Blueprint
from flask import render_template, request, url_for, jsonify, redirect, Response,Markup
from flask.ext.login import login_required, current_user
from pybedtools import BedTool
from app.main import s
from app.views import LockCol,LinkColConditional, LabelCol, LinkColLive, NumberCol
from flask_table import Table, Col, LinkCol
from forms import ViewPanel, CreatePanel, CreatePanelProcess, CreateVirtualPanelProcess, EditVirtualPanelProcess, AddGene, RemoveGene
from queries import *
from app.mod_projects.queries import get_preftx_by_gene_id, get_upcoming_preftx_by_gene_id, get_tx_by_gene_id, add_preftxs_to_panel
import json
import time

panels = Blueprint('panels', __name__, template_folder='templates')

class RegionCol(Col):
    def td(self, item, attr):
        return '<td style="word-wrap: break-word;max-width:800px;">{}</td>'.format(
            self.td_contents(item, self.get_attr_list(attr)))

class ItemTablePanels(Table):
    panelname = Col('Name')
    current_version = Col('Stable Version')
    view_panel = LinkCol('View Panel', 'panels.view_panel', url_kwargs=dict(id='panelid'))
    edit = LinkColConditional('Edit Panel', 'panels.edit_panel_page', url_kwargs=dict(panelid='panelid'))
    view = LinkCol('View Virtual Panels', 'panels.view_virtual_panels', url_kwargs=dict(id='panelid'))
    locked = LockCol('Locked')
    status = LabelCol('Status')
    make_live = LinkColLive('Make Live', 'panels.make_live', url_kwargs=dict(id='panelid'))
    # delete = LinkCol('Delete', 'delete_study', url_kwargs=dict(id='studyid'))


class ItemTableVPanels(Table):
    vp_name = Col('Name')
    current_version = Col('Stable Version')
    view_panel = LinkCol('View Panel', 'panels.view_vpanel', url_kwargs=dict(id='id'))
    edit = LinkColConditional('Edit Panel', 'panels.edit_virtual_panel_process', url_kwargs=dict(id='id'))
    locked = LockCol('Locked')
    status = LabelCol('Status')
    make_live = LinkColLive('Make Live', 'panels.make_virtualpanel_live', url_kwargs=dict(id='id'))
    # delete = LinkCol('Delete', 'delete_study', url_kwargs=dict(id='studyid'))


class ItemTablePanelView(Table):
    allow_sort = False
    chrom = Col('Chromosome')
    region_start = Col('Start')
    region_end = Col('End')
    name = RegionCol('Region Name')
    gene_name = Col('Gene')

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('edit_panel_page', sort=col_key, direction=direction)


class ItemTablePanel(Table):
    allow_sort = False
    status = LabelCol('')
    chrom = Col('Chromosome')
    start = NumberCol('Start', valmin=False)
    end = NumberCol('End', valmin=True)
    number = Col('Exon')
    accession = Col('Accession')
    genename = Col('Gene')
    delete = LinkCol('Delete', 'panels.delete_region', url_kwargs=dict(id='id'))

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('edit_panel_page', sort=col_key, direction=direction)

def isgene(s, gene):
    """
    checks if a gene is in refflad

    :param s: db session
    :param gene: gene name
    :return: true or false
    """
    test = s.query(Genes).filter_by(name=gene).first()
    if test is None:
        return False
    else:
        return True


def check_panel_status(s, id):
    """
    checks the status of a panel - i.e. whether it is live or not live (it has uncommited changes)

    :param s: db session
    :param id: panel id
    :return: true - panel is live or false - panel has changes
    """
    panels = check_panel_status_query(s, id)
    status = True
    for i in panels:
        if i.intro > i.current_version:
            status = False
            break
        if i.last is not None:
            if i.last == i.current_version:
                status = False
                break

    return status

def check_virtualpanel_status(s, id):
    """
    checks the status of a panel - i.e. whether it is live or not live (it has uncommited changes)

    :param s: db session
    :param id: panel id
    :return: true - panel is live or false - panel has changes
    """
    panels = check_virtualpanel_status_query(s, id)
    status = True
    for i in panels:
        if i.intro > i.current_version:
            status = False
            break
        if i.last is not None:
            if i.last == i.current_version:
                status = False
                break

    return status

@panels.route('/download')
@login_required
def download_as_bed():
    scope = request.args.get('scope')
    id = request.args.get('id')
    version = request.args.get('version')
    project_id = request.args.get('project_id')
    panel_name = request.args.get('name')
    permission = check_user_has_permission(s, current_user.id, project_id)

    if scope == 'panel':
        panel = get_regions_by_panelid(s,id,version)
    elif scope == 'virtual_panel':
        pass
        #panel = get_vpanel_by_id(s,id,version=version)

    result = []

    for i in panel:
        line = []
        line.append(i.chrom)
        line.append(str(i.region_start))
        line.append(str(i.region_end))
        line.append(i.name)
        result.append(line)

    bed = '\n'.join(['\t'.join(l) for l in result])

    bed_tool = BedTool(bed, from_string=True)
    bed_sorted = bed_tool.sort()
    bed_sorted_merged = bed_sorted.merge(nms=True)

    result = []
    for i in bed_sorted_merged:
        line = []
        line.append(i.chrom)
        line.append(str(i.start))
        line.append(str(i.end))
        line.append(i.name.replace(";",","))
        result.append(line)

    bed = '\n'.join(['\t'.join(l) for l in result])


    return Response(
        bed,
        mimetype='test/plain',
        headers={"Content-disposition":
                     "attachment; filename="+panel_name+"_v"+version+"_"+current_user.id+"_"+time.strftime("%d-%m-%Y")+".bed"}
    )


@panels.route('/panels', methods=['GET', 'POST'])
@login_required
# @lock_check
def view_panels(id=None):
    """
    method to view panels, if project ID given then only return panels from that project
    matt
    :param id: project id
    :return: rendered template panels.html
    """
    if not id:
        id = request.args.get('id')
    if id:
        panels = get_panels_by_project_id(s, id)
    else:
        panels = get_panels(s)
    result = []
    project_name = "All"
    for i in panels:
        row = dict(zip(i.keys(), i))
        status = check_panel_status(s, row["panelid"])
        row["status"] = status
        permission = check_user_has_permission(s, current_user.id, row["projectid"])
        locked = check_if_locked_by_user(s, current_user.id, row["panelid"])
        row["conditional"] = None
        if permission is True and locked is True:
            row["conditional"] = True
        if permission is True and locked is False:
            row["conditional"] = False
        if permission is False and locked is False:
            row["conditional"] = False
        if id:
            project_name = row['projectname']
        # if check_user_has_permission(s, current_user.id, row["projectid"]):
        #     result.append(row)
        result.append(row)
    table = ItemTablePanels(result, classes=['table', 'table-striped'])
    return render_template('panels.html', panels=table, project_name=project_name)


@panels.route('/panel', methods=['GET', 'POST'])
@login_required
def view_panel():
    id = request.args.get('id')
    try:
        version = request.form["versions"]
    except KeyError:
        version = None
    if id:
        status = check_panel_status(s, id)
        if not status:
            message = "This panel has changes which cannot be viewed here as they have not been made live yet, if you have permission you can view these by editing the panel"
        else:
            message = None
        panel_details = get_panel_details_by_id(s, id)
        for i in panel_details:
            if not version:
                version = i.current_version
            panel_name = i.name
        panel = get_regions_by_panelid(s, id, version)
        project_id = get_project_id_by_panel_id(s, id)
        result = []
        rows = list(panel)
        if len(rows) != 0:
            bed = ''
            for i in rows:
                row = dict(zip(i.keys(), i))
                result.append(row)
                panel_name = i.panel_name
                current_version = i.current_version
            table = ItemTablePanelView(result, classes=['table', 'table-striped','table-nonfluid'])
        else:
            table = ""
            message = "This Panel has no regions yet & may also have changes that have not been made live"
            bed = 'disabled'
            current_version = version

        if check_user_has_permission(s, current_user.id, project_id):
            edit = ''
        else:
            edit = 'disabled'

        form = ViewPanel()
        v_list = range(1,current_version + 1)
        choices = []
        for i in v_list:
            choices.append((i, i))
        form.versions.choices = choices
        form.versions.default = current_version
        form.process()

        table=[]

        for i in result:
            line=[]
            line.append(i['chrom'])
            line.append(str(i['region_start']))
            line.append(str(i['region_end']))
            line.append(i['gene_name'])
            line.append(i['name'].replace(',',' '))
            table.append(line)

        return render_template('panel_view.html', table=json.dumps(table),panel=table, panel_name=panel_name, edit=edit, bed=bed,
                               version=version, panel_id=id, project_id=project_id, message=message, url = url_for('panels.view_panel'),
                               form=form)

    else:
        return redirect(url_for('panels.view_panels'))

@panels.route('/create', methods=['GET', 'POST'])
@login_required
def create_panel():
    form = CreatePanel()
    if request.method == 'POST':
        # if form.validate() == False:
        #     flash('All fields are required.')
        #     return render_template('panel_create.html', form=form)
        # else:
        panelname = request.form["panelname"]
        project = request.form["project"]
        genesraw = request.form["listgenes"]
        genes = genesraw.rstrip(',').split(",")

        result = []
        for gene in genes:
            test = isgene(s, gene)
            result.append(test)

        if False not in result:
            test_panel = s.query(Panels).filter_by(name=panelname).first()
            if test_panel is not None:
                return render_template('panel_create.html', form=form, message="Panel Name Exists")
            else:
                id = create_panel_query(s, project, panelname, current_user.id)

                for gene in genes:
                    add_genes_to_panel(s, id, gene)
                return redirect(url_for('edit_panel_page', id=id))
        else:
            return render_template('panel_create.html', form=form, message="One or more Gene Name(s) Invalid")

    elif request.method == 'GET':
        return render_template('panel_create.html', form=form)

@panels.route('/panels/wizard', methods=['GET', 'POST'])
@login_required
def create_panel_process():
    """

    :return:
    """
    form = CreatePanelProcess()
    if request.method == "POST":
        pass
    elif request.method == "GET":
        print('get wizard')
        return render_template('panel_createprocess.html', form=form, panel_id="main", url=url_for('panels.create_panel_process'))

@panels.route('/panels/add',  methods=['POST'])
@login_required
def add_panel():
    """

    :return:
    """
    panel_name = request.json['panel_name']
    project_id = request.json['project_id']
    panel_id = create_panel_query(s, project_id, panel_name, current_user.id)
    return jsonify(panel_id)

@panels.route('/panels/remove',  methods=['POST'])
@login_required
def remove_panel():
    """

    :return:
    """
    panel_name = request.json['panel_name']
    remove_panel_query(s, panel_name)
    return jsonify('complete')

@panels.route('/panels/upload', methods=['POST'])
@login_required
def upload_multiple():
    """

    :return:
    """
    gene_list = request.json['gene_list'].replace('\r','').split('\n')
    project_id = request.json['project_id']
    all_message = ''
    html = ''
    added_list = []
    button_list = ''

    for gene in gene_list:
        if gene == "":
            continue
        dct = create_panel_get_tx(gene, project_id)
        print(dct["message"])
        if dct["message"] == "added":
            added_list.append(gene)
        else:
            all_message += dct["message"]
        try:
            print(dct["html"])
            html += dct["html"]
        except KeyError:
            pass
        try:
            print(dct["button_list"])
            button_list += dct["button_list"]
        except KeyError:
            pass

    added_message = "<div class =\"alert alert-success\" name=\"message-fade\"><strong>FYI</strong> "

    for g in added_list:
        if added_list.index(g) == len(added_list) -1:
            string = "and " + g
            added_message += string
        else:
            string = g + ", "
            added_message += string

    added_message += " have been added</div>"
    all_message += added_message
    return jsonify({'message':all_message, 'html':html, 'button_list':button_list})


@panels.route('/panels/preftx', methods=['POST'])
@login_required
def create_panel_get_tx(gene_name=None, project_id=None):
    """

    :return:
    """
    json=False
    print(gene_name)
    if not gene_name:
        gene_name = request.json['gene_name']
        project_id = request.json['project_id']
        json=True
    exists = isgene(s, gene_name)

    if exists:
        gene_id = get_gene_id_from_name(s, gene_name)
        preftx_id = get_preftx_by_gene_id
        upcoming_preftx = get_upcoming_preftx_by_gene_id(s, project_id, gene_id)
        all_tx = get_tx_by_gene_id(s, gene_id)
        html = """<tr>
                    <td>
                        <label for=\"""" + gene_name + "\">" + gene_name + """</label>
                    </td>
                    <td>
                        <div class=\"form-group\">
                        <select class=\"form-control\" name=\"""" + gene_name + "\" id=\"" + gene_name + "\">"

        gene_button = "<button name=\"genebutton\" type=\"button\" class=\"btn btn-success btn-md btngene\" data-name=\"" + \
                      gene_name + "\" data-id=\"" + str(gene_id) + "\"><span class='glyphicon glyphicon-ok'></span> " + \
                      gene_name + "</button> "

        for tx in all_tx:
            print(tx)
            if upcoming_preftx == tx.id:

                html = """<tr>
                    <td>
                        <label for=\"""" + gene_name + "\">" + gene_name + """</label>
                    </td>
                    <td>
                        <div class=\"form-group\">
                        <select class=\"form-control\" name=\"""" + gene_name + "\" id=\"" + gene_name + "\">" +\
                        "<option value=\"" + str(tx.id) + "\" class=\"red\">" + tx.accession + " - This Is a Change Not Made Live Yet</option>" + \
                            """</select>
                                 </div>
                                    </td>
                            </tr>"""
                print(html)


                success_message = "<div class =\"alert alert-success\" name=\"message-fade\"><strong>FYI</strong> " + gene_name + " was added</div>"
                if json:
                    return jsonify({'html':html, 'button_list':gene_button, 'message':success_message})
                else:
                    return {'html': html, 'button_list': gene_button, 'message': "added"}
            else:
                html += "<option value=\"" + str(tx.id) + "\""

                if preftx_id == tx.id:
                    html +=  " class=\"bolden\" selected"
                else:
                    html += " class=\"\""

            html += ">" + tx.accession + "</option>"
        html += """</select>
                    </div>
                </td>
            </tr>"""

        print(html)
        success_message = "<div class =\"alert alert-success\" name=\"message-fade\"><strong>FYI</strong> " + gene_name + " was added</div>"

        if json:
            return jsonify({'html': html, 'button_list': gene_button, 'message': success_message})
        else:
            return {'html': html, 'button_list': gene_button, 'message': "added"}
    else:
        fail_message = "<div class =\"alert alert-danger\" name=\"" + gene_name + "\" id=\"message-fail\"><strong>Oh Crumbs!</strong> " + gene_name + " didn't match anything in the database</div>"
        if json:
            return jsonify({'message': fail_message})
        else:
            return {'message': fail_message}

@panels.route('/panels/custom/create', methods=['POST'])
@login_required
def create_panel_custom_regions():
    """
    Creates a custom region from ajax query and adds region to versions table for specified panel

    :return:
    """
    panel_id = request.json["panel_id"]
    chrom = request.json["chrom"]
    start = request.json["start"]
    end = request.json["end"]
    name = request.json["name"]
    regions = select_region_by_location(s, chrom, start, end)#if region already exists, return current entry
    if regions:
        for i in regions:
            v_id = add_region_to_panel(s, i.id, panel_id)
            region = i
            continue
    else:
        region, v_id = create_custom_region(s, panel_id, chrom, start, end, name)

    row = """<tr>
                        <td><label for=\"""" + v_id + "\">" + v_id + "</label></td>" + \
          "<td>" + region.chrom + "</td>" + \
          "<td>" + str(region.start) + "</td>" + \
          "<td>" + str(region.end) + "</td>" + \
          "<td style=\"word-wrap: break-word\">" + region.name + "</td>" + \
          """<td><div class=\"material-switch pull-right\">
                  <input type=\"checkbox\" id=\"""" + v_id + """\" name=\"region-check\">
                                <label for=\"""" + v_id + """\" class=\"label-success label-region\" ></label>
                            </div></td>
                    </tr>"""

    return jsonify(row)

@panels.route('/panels/add_regions', methods=['POST'])
@login_required
def add_panel_regions():
    version_ids = request.json['ids']
    print(version_ids)
    panel_id = request.json['panel_id']
    tx_id = request.json['pref_tx_id']
    project_id = request.json['project_id']
    gene_name = request.json['gene_name']

    add_preftxs_to_panel(s, project_id, [{"gene":gene_name, "tx_id":tx_id},])

    for i in version_ids:
        add_region_to_panel(s, i, panel_id)
    s.commit()
    return jsonify("complete")

@panels.route('/panels/remove_regions', methods=['POST'])
@login_required
def remove_panel_regions():
    """

    :return:
    """
    version_ids = request.json['ids']
    if type(version_ids) is str:
        version_ids = version_ids.split(',')
    print(version_ids)
    panel_id = request.json['panel_id']

    for i in version_ids:
        print(i)
        remove_version_from_panel(s, int(panel_id), int(i))

    panel = get_panel_by_id(s, panel_id)#check if there are still regions in the panel
    length = len(list(panel))
    return jsonify(length)

@panels.route('/live', methods=['GET', 'POST'])
@login_required
def make_live():
    """
    given a panel id this method makes a panel live

    :return: redirection to view panels
    """
    panelid = request.args.get('id')
    current_version = get_current_version(s, panelid)
    new_version = current_version + 1
    make_panel_live(s, panelid, new_version, current_user.id)
    return redirect(url_for('panels.view_panels'))


@panels.route('/unlock')
@login_required
def unlock_panel():
    panelid = request.args.get('panelid')
    unlock_panel_query(s, panelid)

    return redirect(url_for('panels.view_panels'))


@panels.route('/edit')
@login_required
def edit_panel_page(panel_id=None):
    id = request.args.get('panelid')
    lock_panel(s, current_user.id, id)
    if id is None:
        id = panel_id
    panel_info = s.query(Panels, Projects).join(Projects).filter(Panels.id == id).values(
        Panels.current_version,
        Panels.name,
        Panels.locked
    )
    print panel_info
    for i in panel_info:
        version = i.current_version
        name = i.name
    panel = get_panel_edit(s, id=id, version=version)
    form = RemoveGene(panelId=id)
    add_form = AddGene(panelIdAdd=id)

    result = []
    genes = []
    for i in panel:
        row = dict(zip(i.keys(), i))
        row['original_start'] = row["start"]
        row['original_end'] = row["end"]
        if row["intro"] > row["current_version"]:
            row["status"] = False
        else:
            row["status"] = True
        result.append(row)
        if row["extension_5"]:
            row["start"] = int(row["start"]) + int(row["extension_5"])
        if row["extension_3"]:
            row["end"] = int(row["end"]) + int(row["extension_3"])
        genes.append(Markup("<button type=\"button\" class=\"btn btn-danger btn-md btngene\" data-id=\"" + str(
            i.panelid) + "\" data-name=\"" + i.genename + "\" data-toggle=\"modal\" data-target=\"#removeGene\" id=\"myDeleteButton\"><span class=\"glyphicon glyphicon-remove\"></span> " + i.genename + "</button>"))
    table = ItemTablePanel(result, classes=['table', 'table-striped'])
    return render_template('panel_edit.html', panel_name=name, version=version,
                           panel_detail=table, genes=" ".join(sorted(set(genes))), form=form, add_form=add_form,
                           panel_id=id)


@panels.route('/edit', methods=['POST', 'GET'])
@login_required
def edit_panel():
    if request.method == 'POST':
        panel_id = request.form["panel_id"]
        for v in request.form:
            if v.startswith("region"):
                value = int(request.form[v])
                region, region_id, intro, last, current_version, id, start, ext_5, end, ext_3, scope = v.split("_")
                if ext_5:
                    original_start = int(start) + int(ext_5)
                else:
                    original_start = start
                if ext_3:
                    original_end = int(end) + int(ext_3)
                else:
                    original_end = end
                if scope == "start":

                    if value != int(original_start):


                        extension_5 = int(value) - int(original_start)
                        check = s.query(Versions).filter_by(region_id=region_id,
                                                                   intro=int(current_version) + 1).count()

                        if check > 0:
                            s.query(Versions).filter_by(region_id=region_id,
                                                               intro=int(current_version) + 1).update(
                                {Versions.extension_5: extension_5})
                            s.commit()
                        else:
                            s.query(Versions).filter_by(id=id).update({Versions.last: current_version})
                            s.commit()
                            v = Versions(intro=int(current_version) + 1, last=None, panel_id=int(panel_id),
                                                comment=None,
                                                extension_3=None, extension_5=int(extension_5),
                                                region_id=int(region_id))
                            s.add(v)
                            s.commit()
                if scope == "end":
                    if value != int(original_end):
                        print "hello"
                        extension_3 = int(value) - int(original_end)

                        check = s.query(Versions).filter_by(region_id=region_id,
                                                                   intro=int(current_version) + 1).count()
                        if check > 0:
                            s.query(Versions).filter_by(region_id=region_id,
                                                               intro=int(current_version) + 1).update(
                                {Versions.extension_3: extension_3})
                            s.commit()
                        else:
                            s.query(Versions).filter_by(id=id).update({Versions.last: current_version})
                            s.commit()
                            v = Versions(intro=int(current_version) + 1, last=None, panel_id=int(panel_id),
                                                comment=None,
                                                extension_3=extension_3, extension_5=None,
                                                region_id=int(region_id))
                            s.add(v)
                            s.commit()
    return edit_panel_page(panel_id=panel_id)


@panels.route('/delete/gene', methods=['POST'])
@login_required
def remove_gene():
    #s = scoped_session(db.session)
    form = RemoveGene()
    if request.method == 'POST':
        id = form.data['panelId']
        gene = form.data['geneName']
        panel_info = get_panel_edit(s, id, 1)
        ids = []
        for i in panel_info:
            if i.genename == gene:
                # todo add if in here - if the gene is not already in a live panel it is okay to delete completely
                s.query(Versions).filter_by(id=i.id).update({Versions.last: i.current_version})
                ids.append(i.id)
    s.commit()
    return edit_panel_page(id)


@panels.route('/delete/gene', methods=['POST'])
@login_required
def delete_region():
    pass
    return edit_panel_page(id)


@panels.route('/delete/add', methods=['POST'])
@login_required
def add_gene():
    """
    adds a gene to a panel
    :return: edit panel page
    """
    form = AddGene()
    if request.method == 'POST':
        id = form.data['panelIdAdd']
        gene = form.data['genes']
        if isgene(s, gene):
            add_genes_to_panel(s, id, gene)
    return edit_panel_page(id)



#################
# VIRTUAL PANELS
################

@panels.route('/virtualpanels', methods=['GET','POST'])
@login_required
def view_virtual_panels(id=None):
    """
       method to view panels, if project ID given then only return panels from that project
       matt
       :param id: project id
       :return: rendered template panels.html
       """
    if not id:
        id = request.args.get('id')
    if id:
        panels = get_virtual_panels_by_panel_id(s, id)
    else:
        panels = get_virtual_panels_simple(s)
    result = []
    panel_name = "Virtual"
    for i in panels:
        row = dict(zip(i.keys(), i))

        status = check_virtualpanel_status(s, row["id"])
        row["status"] = status
        permission = check_user_has_permission(s, current_user.id, row["projectid"])
        locked = check_if_locked_by_user(s, current_user.id, row["panelid"])
        row["conditional"] = None
        if permission is True and locked is True:
            row["conditional"] = True
        if permission is True and locked is False:
            row["conditional"] = False
        if permission is False and locked is False:
            row["conditional"] = False


        if id:
            panel_name = row['panelname'] + ' Virtual'
        # if check_user_has_permission(s, current_user.id, row["projectid"]):
        #     result.append(row)
        result.append(row)
    table = ItemTableVPanels(result, classes=['table', 'table-striped'])
    return render_template('panels.html', panels=table, project_name=panel_name,
                           message='Virtual Panels are locked if their parent panel is being edited')

@panels.route('/vpanel', methods=['GET', 'POST'])
@login_required
def view_vpanel():
    id = request.args.get('id')
    try:
        version = request.form["versions"]
    except KeyError:
        version = None
    if id:
        status = check_virtualpanel_status(s, id)
        if not status:
            message = "This panel has changes which cannot be viewed here as they have not been made live yet, if you have permission you can view these by editing the panel"
        else:
            message = None
        panel_details = get_vpanel_details_by_id(s, id)
        for i in panel_details:
            if not version:
                version = i.current_version
            panel_name = i.name
            project_id = i.project_id
        panel = get_vpanel_by_id(s, id)
        result = []
        rows = list(panel)
        if len(rows) != 0:
            bed = ''
            for i in rows:
                row = dict(zip(i.keys(), i))
                # status = check_panel_status(s, row["panelid"])
                # row["status"] = status
                result.append(row)
                panel_name = row["name"]
                current_version = row["current_version"]
            table = ItemTablePanelView(result, classes=['table', 'table-striped'])
        else:
            table = ""
            message = "This Panel has no regions yet & may also have chnages that have not been made live yet"
            bed = 'disabled'
            current_version = version
        print 'version'
        print current_version

        if check_user_has_permission(s, current_user.id, project_id):
            edit = ''
        else:
            edit = 'disabled'

        form = ViewPanel()
        v_list = range (1, current_version+1)
        choices = []
        for i in v_list:
            choices.append((i,i))
        form.versions.choices = choices
        form.versions.default = current_version
        form.process()
        return render_template('panel_view.html', panel=table, panel_name=panel_name, edit=edit, bed=bed,
                                version=version, panel_id=id, message=message, url= url_for('panels.view_vpanel'),
                                scope='Virtual', form=form)

    else:
        return redirect(url_for('panels.view_vpanels'))

@panels.route('/virtualpanels/wizard', methods=['GET', 'POST'])
@login_required
def create_virtual_panel_process():
    """

    :return:
    """
    form = CreateVirtualPanelProcess()

    if request.method == "POST":
        make_live = request.form['make_live']
        vp_id = request.args.get('id')
        if make_live == "True":
            make_vp_panel_live(s, vp_id, 1)
        panel_id = get_panel_by_vp_id(s, vp_id)
        unlock_panel_query(s, panel_id)
        return redirect(url_for('panels.view_virtual_panels'))
    elif request.method == "GET":
        url = url_for('panels.create_virtual_panel_process')
        return render_template('virtualpanels_createprocess.html', form=form, url=url, vp_id="main")

@panels.route('/virtualpanels/edit', methods=['GET', 'POST'])
@login_required
def edit_virtual_panel_process():
    """

    :return:
    """
    form = EditVirtualPanelProcess()

    vp_id = request.args.get('id')
    panel_id = get_panel_by_vp_id(s, vp_id)
    if request.method == "POST":
        if make_live == "True":
            make_vp_panel_live(s, vp_id, 1)
        unlock_panel_query(s, panel_id)
        return redirect(url_for('panels.view_virtual_panels'))
    elif request.method == "GET":
        lock_panel(s, current_user.id, panel_id)
        panel_info = get_panel_details_by_id(s,panel_id)
        panel_name = ""
        for i in panel_info:
            panel_name = i.name
        form.panel.choices = [(panel_id, panel_name)]

        panel_version = get_current_version(s, panel_id)
        panel_genes = get_genes_by_panelid(s, panel_id, panel_version)
        vp_info = get_vpanel_details_by_id(s, vp_id)
        print(vp_info)
        vp_version = vp_info.current_version
        vp_name = vp_info.name
        form.vpanelname.data = vp_name
        vp_genes = get_genes_by_vpanelid(s, vp_id, vp_version)
        gene_html = ""
        genelist = ""
        vp_list = []
        for i in vp_genes:
            vp_list.append(i.id)

        for i in panel_genes:
            if i.id in vp_list:
                line = "<li class=\"list-group-item\">" + \
                       i.name + \
                       "<div class=\"material-switch pull-right\"><input type=\"checkbox\" name=\"" + str(i.id) + \
                       "\" id=\"" + i.name + "\" disabled=\"disabled\" checked=\"checked\"><label for=\"" + i.name + \
                       "\" class=\"label-added label-gene\" disabled=\"disabled\"></label></div></li>"
                button = "<button name=\"genebutton\" type=\"button\" class=\"btn btn-success btn-md btngene\" data-name=\"" +\
                         i.name + "\" data-id=\"" + str(i.id) + "\"><span class='glyphicon glyphicon-ok'></span> " + \
                         i.name + "</button> "
                genelist += button

            else:
                line = "<li class=\"list-group-item\">" + \
                       i.name + \
                       "<div class=\"material-switch pull-right\"><input type=\"checkbox\" name=\"" + str(i.id) +\
                       "\" id=\"" + i.name + "\"><label for=\"" + i.name +\
                       "\" class=\"label-success label-gene\"></label></div></li>"
            gene_html += line

        url = url_for('panels.edit_virtual_panel_process')
        return render_template('virtualpanels_createprocess.html', form=form, genes=gene_html, genelist=genelist, vp_id = vp_id, panel_name=vp_name, current_version=vp_version, url=url)

@panels.route('/virtualpanels/add',  methods=['POST'])
@login_required
def add_vp():
    """

    :return:
    """
    vp_name = request.json['vp_name']
    panel_id = request.json['panel_id']
    vp_id = create_virtualpanel_query(s, vp_name)
    if vp_id != -1:
        lock_panel(s, current_user.id, panel_id)
    return jsonify(vp_id)

@panels.route('/virtualpanels/remove',  methods=['POST'])
@login_required
def remove_vp():
    """

    :return:
    """
    vp_name = request.json['vp_name']
    remove_virtualpanel_query(s, vp_name)
    return jsonify('complete')


@panels.route('/virtualpanels/select', methods=['POST'])
@login_required
def select_vp_genes():
    """

    :return:
    """
    panel_id = request.json["panel"]
    current_version = get_current_version(s, panel_id)

    genes = get_genes_by_panelid(s, panel_id, current_version)

    html = ""
    for gene in genes:

        line = "<li class=\"list-group-item\">" + \
               gene.name + \
               "<div class=\"material-switch pull-right\"><input type=\"checkbox\" name=\"" + str(gene.id) + "\" id=\"" + \
               gene.name + "\"><label for=\"" + gene.name + "\" class=\"label-success label-gene\"></label></div></li>"
        html += line
    print(html)
    return jsonify(html)

@panels.route('/virtualpanels/custom', methods=['POST'])
@login_required
def get_custom_regions():
    """

    :return:
    """
    panel_id = request.json["panel_id"]
    vpanel_id = request.json["vpanel_id"]
    current_regions = []

    regions = get_custom_regions_query(s, panel_id)
    html = """<h3 name=\"Custom\">Custom Regions</h3><ul class=\"list-unstyled list-inline pull-right\">
                        <li>
                            <button type=\"button\" class=\"btn btn-success\" id=\"add-regions\" name=\"Custom\" disabled=\"disabled\">Add Regions</button>
                        </li>
                    </ul>

                <table class=\"table table-striped\">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Chrom</th>
                            <th>Region Start</th>
                            <th>Region End</th>
                            <th>Names</th>
                            <th>Select All <div class="material-switch pull-right">
                                                <input type="checkbox" id="checkAll">
                                                <label for="checkAll" class="label-success label-selectall"></label>
                                            </div>
                            </th>
                        </tr>
                    </thead>"""
    for i in regions:
        if not vpanel_id:
            current_regions.append(i.id)
        print(i.name)
        v_id = str(i.version_id)
        row = """<tr>
                        <td><label for=\"""" + v_id + "\">" + v_id + "</label></td>" + \
              "<td>" + i.chrom + "</td>" + \
              "<td>" + str(i.region_start) + "</td>" + \
              "<td>" + str(i.region_end) + "</td>" + \
              "<td style=\"word-wrap: break-word\">" + i.name.replace(',', '\n') + "</td>" + \
              """<td><div class=\"material-switch pull-right\">
                      <input type=\"checkbox\" id=\"""" + v_id + """\" name=\"region-check\">
                                <label for=\"""" + v_id + """\" class=\"label-success label-region\" ></label>
                            </div></td>
                    </tr>"""
        html += row

    if vpanel_id:
        version_ids = get_current_custom_regions(s, vpanel_id)
        for i in version_ids:
            current_regions.append(i[0])

    html += "</table>"
    return jsonify({'html':html, 'ids':current_regions})

@panels.route('/virtualpanels/getregions', methods=['POST'])
def select_vp_regions(gene_id=None, gene_name=None, panel_id=None):
    """

    :return:
    """
    json = False
    if not gene_id:
        json = True
        print(request.json)
        gene_id = request.json['gene_id']
        gene_name = request.json['gene_name']
        panel_id = request.json['panel_id']
    if panel_id:
        regions = get_panel_regions_by_geneid(s, gene_id, panel_id)
    else:
        print("gene regions")
        regions = get_regions_by_geneid(s, gene_id)
    html = "<h3 name=\"" + gene_id + "\">" + gene_name + """</h3><ul class=\"list-unstyled list-inline pull-right\">
                    <li>
                        <button type=\"button\" class=\"btn btn-success\" id=\"add-regions\" name=\"""" + gene_name + """\" disabled=\"disabled\">Add Regions</button>
                    </li>
                    <li>
                        <button type=\"button\" class=\"btn btn-danger\" id=\"remove-gene\" name=\"""" + gene_name + """\">Remove Gene</button>
                    </li>
                </ul>

            <table class=\"table table-striped\">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Chrom</th>
                        <th>Region Start</th>
                        <th>Region End</th>
                        <th>Names</th>
                        <th>Select All <div class="material-switch pull-right">
                                            <input type="checkbox" id="checkAll">
                                            <label for="checkAll" class="label-success label-selectall"></label>
                                        </div>
                        </th>
                    </tr>
                </thead>"""
    for i in regions:
        print(i.name)
        if panel_id:
            v_id = str(i.version_id)
        else:
            v_id = str(i.region_id)

        row = """<tr>
                    <td><label for=\"""" +  v_id + "\">" + v_id + "</label></td>" +\
                    "<td>" + i.chrom + "</td>" + \
                    "<td>" + str(i.region_start) + "</td>" + \
                    "<td>" + str(i.region_end) + "</td>" + \
                    "<td style=\"word-wrap: break-word\">" + i.name.replace(',', '\n') + "</td>" + \
                    """<td><div class=\"material-switch pull-right\">
                            <input type=\"checkbox\" id=\"""" + v_id + """\" name=\"region-check\">
                            <label for=\"""" + v_id + """\" class=\"label-success label-region\" ></label>
                        </div></td>
                </tr>"""
        html += row

    html += "</table>"

    if json:
        return jsonify(html)
    else:
        return html

@panels.route('/virtualpanels/editregions', methods=['POST'])
def edit_vp_regions():
    """

    :return:
    """
    print(request.json)
    gene_id = request.json['gene_id']
    gene_name = request.json['gene_name']
    panel_id = request.json['panel_id']
    vpanel_id = request.json['vpanel_id']

    if vpanel_id:
        print("virtual")
        html = select_vp_regions(gene_id, gene_name, panel_id)
        regions = get_vprelationships(s, vpanel_id, gene_id)
    else:
        print("panel")
        html = select_vp_regions(gene_id, gene_name)
        regions = get_versions(s, panel_id, gene_id)
    version_ids = []
    for i in regions:
        print(i[0])
        version_ids.append(i[0])
    print(version_ids)
    dict = {'html':html,'ids':version_ids}

    return jsonify(dict)

@panels.route('/virtualpanels/add_regions', methods=['POST'])
@login_required
def add_vp_regions():
    version_ids = request.json['ids']
    vpanel_id = request.json['vp_id']
    for i in version_ids:
        add_version_to_vp(s, vpanel_id, i)
    return jsonify("complete")

@panels.route('/virtualpanels/remove_regions', methods=['POST'])
@login_required
def remove_vp_regions():
    """

    :return:
    """
    version_ids = request.json['ids']
    if type(version_ids) is str:
        version_ids = version_ids.split(',')
    print(version_ids)
    vpanel_id = request.json['vp_id']
    print(vpanel_id)

    for i in version_ids:
        print(i)
        remove_version_from_vp(s, int(vpanel_id), int(i))

    panel = get_vpanel_by_id(s, vpanel_id)
    length = len(list(panel))
    return jsonify(length)

@panels.route('/virtualpanels/live', methods=['GET', 'POST'])
def make_virtualpanel_live():
    """
    given a panel id this method makes a panel live

    :return: redirection to view panels
    """
    panelid = request.args.get('id')
    current_version = get_current_version_vp(s, panelid)
    new_version = current_version + 1
    make_vp_panel_live(s, panelid, new_version)

    return redirect(url_for('view_virtual_panels'))


@panels.route('/virtualpanels/delete', methods=['GET', 'POST'])
def delete_virtualpanel():
    u = db.session.query(VirtualPanels).filter_by(id=request.args.get('id')).first()
    db.session.delete(u)
    db.session.commit()
    return view_virtual_panels()


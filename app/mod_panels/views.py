from app.queries import *
from flask import Blueprint
from flask import render_template, request, url_for, jsonify, redirect, Response,Markup
from flask.ext.login import login_required, current_user

from app.main import s
from app.views import LockCol,LinkColConditional, LabelCol, LinkColLive, NumberCol
from flask_table import Table, Col, LinkCol
from forms import ViewPanel, CreatePanel, CreateVirtualPanelProcess, AddGene, RemoveGene
from queries import *


panels = Blueprint('panels', __name__, template_folder='templates')

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
    view_panel = LinkCol('View Panel', 'panels.view_virtual_panel', url_kwargs=dict(id='id'))
    edit = LinkColConditional('Edit Panel', 'panels.edit_panel_page', url_kwargs=dict(id='id'))
    locked = LockCol('Locked')
    status = LabelCol('Status')
    make_live = LinkColLive('Make Live', 'panels.make_virtualpanel_live', url_kwargs=dict(id='id'))
    # delete = LinkCol('Delete', 'delete_study', url_kwargs=dict(id='studyid'))


class ItemTablePanelView(Table):
    allow_sort = False
    chrom = Col('Chromosome')
    start = Col('Start')
    end = Col('End')
    number = Col('Exon')
    accession = Col('Accession')
    genename = Col('Gene')

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
    delete = LinkCol('Delete', 'delete_region', url_kwargs=dict(id='id'))

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('edit_panel_page', sort=col_key, direction=direction)

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
    bed = "test\ttest\ttest"
    return Response(
        bed,
        mimetype='test/plain',
        headers={"Content-disposition":
                     "attachment; filename=test.bed"}
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
        print 'version'
        print version
        panel = get_panel_by_id(s, id, version)
        project_id = get_project_id_by_panel_id(s, id)
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
        return render_template('panel_view.html', panel=table, panel_name=panel_name, edit=edit, bed=bed,
                               version=version, panel_id=id, message=message, url = url_for('panels.view_panel'),
                               form=form)

    else:
        return redirect(url_for('panels.view_panels'))


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
                id = create_panel_query(s, project, panelname)

                for gene in genes:
                    add_genes_to_panel(s, id, gene)
                return redirect(url_for('edit_panel_page', id=id))
        else:
            return render_template('panel_create.html', form=form, message="One or more Gene Name(s) Invalid")

    elif request.method == 'GET':
        return render_template('panel_create.html', form=form)


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
        return redirect(url_for('view_virtual_panels'))
    elif request.method == "GET":
        return render_template('virtualpanels_createprocess.html', form=form, tab=1)

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

@panels.route('/virtualpanels/getregions', methods=['POST'])
def select_vp_regions():
    """

    :return:
    """
    print(request.json)
    gene_id = request.json['gene_id']
    gene_name = request.json['gene_name']
    panel_id = request.json['panel_id']
    regions = get_regions_by_geneid(s, gene_id, panel_id)
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
        v_id = str(i.version_id)
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

    return jsonify(html)

@panels.route('/virtualpanels/add_regions', methods=['POST'])
@login_required
def add_vp_regions():
    version_ids = request.json['ids']
    vpanel_id = request.json['vp_id']
    for i in version_ids:
        rel_id = add_version_to_vp(s, vpanel_id, i)
    return jsonify("complete")

@panels.route('/virtualpanels/view', methods=['GET', 'POST'])
def view_virtual_panel():
    """

    :return:
    """

@panels.route('/virtualpanels/live', methods=['GET', 'POST'])
def make_virtualpanel_live():
    """
    given a panel id this method makes a panel live

    :return: redirection to view panels
    """
    panelid = request.args.get('id')
    current_version = get_current_vp_version(s, panelid)
    new_version = current_version + 1
    make_vp_panel_live(s, panelid, new_version)

    return redirect(url_for('view_virtual_panels'))


@panels.route('/virtualpanels/delete', methods=['GET', 'POST'])
def delete_virtualpanel():
    u = db.session.query(VirtualPanels).filter_by(id=request.args.get('id')).first()
    db.session.delete(u)
    db.session.commit()
    return view_virtual_panels()


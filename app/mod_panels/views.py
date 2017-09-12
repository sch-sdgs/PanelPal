from flask import Blueprint
from flask import render_template, request, url_for, jsonify, redirect, Response
from flask_login import login_required, current_user
from pybedtools import BedTool
from app.panel_pal import s, Session
from app.mod_projects.views import LinkColConditional
from flask_table import Table, Col, LinkCol
from forms import ViewPanel, CreatePanelProcess, EditPanelProcess, CreateVirtualPanelProcess, \
    EditVirtualPanelProcess
from queries import *
from app.mod_projects.queries import get_preftx_by_gene_id, get_upcoming_preftx_by_gene_id, get_tx_by_gene_id, \
    add_preftxs_to_panel, make_preftx_live, get_current_preftx_version, get_preftx_id_by_project_id
from app.mod_admin.queries import get_username_by_user_id, check_user_has_permission
import json
import time

panels = Blueprint('panels', __name__, template_folder='templates')

class NumberCol(Col):
    def __init__(self, name, valmin=False, attr=None, attr_list=None, **kwargs):
        self.valmin = valmin
        super(NumberCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td_contents(self, item, attr_list):
        """
        special td contents for editing a panel - so includes form input fields etc
        :param item:
        :param attr_list:
        :return:
        """
        id = "region_" + str(self.from_attr_list(item, ['region_id'])) + "_" + str(
            self.from_attr_list(item, ['intro'])) + "_" + str(
            self.from_attr_list(item, ['last'])) + "_" + str(
            self.from_attr_list(item, ['current_version'])) + "_" + str(self.from_attr_list(item, ['id'])) + "_" + str(
            self.from_attr_list(item, ['original_start'])) + "_" + str(
            self.from_attr_list(item, ['extension_5'])) + "_" + str(
            self.from_attr_list(item, ['original_end'])) + "_" + str(
            self.from_attr_list(item, ['extension_3'])) + "_" + str(attr_list[0])
        # todo add an id to teh input class so you can check if starts are less than ends?
        return '<input class="form-control" value="{number}" name="{id}">'.format(
            number=self.from_attr_list(item, attr_list), id=id)


class LockCol(Col):
    def __init__(self, name, attr=None, attr_list=None, **kwargs):
        super(LockCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td_contents(self, item, attr_list):
        if item["locked"] is not None:
            username = get_username_by_user_id(s, item["locked"])
            return '<center><span class="glyphicon glyphicon-lock"  data-toggle="tooltip" data-placement="bottom" title="Locked by: ' + username + '" aria-hidden="true"></span></center>'
        else:
            return ''

class LinkColEdit(LinkCol):
    def td_contents(self, item, attr_list):
        if (item["locked"] is None or current_user.id == get_username_by_user_id(s, item["locked"])) and item["permission"] is True:
            return '<a href="{url}">{text}</a>'.format(
                url=self.url(item),
                text=self.td_format(self.text(item, attr_list)))
        else:
            return '-'

class LinkColLive(LinkCol):
    def td_contents(self, item, attr_list):
        if (item["locked"] is None or current_user.id == get_username_by_user_id(s,item["locked"])) and item["permission"] is True and item["status"] is False:
            return '<a href="{url}">{text}</a>'.format(
                url=self.url(item),
                text=self.td_format(self.text(item, attr_list)))
        else:
            return '-'

class RegionCol(Col):
    def td(self, item, attr):
        return '<td style="word-wrap: break-word;max-width:800px;">{}</td>'.format(
            self.td_contents(item, self.get_attr_list(attr)))

class LabelCol(Col):
    def __init__(self, name, valmin=False, attr=None, attr_list=None, **kwargs):

        self.valmin = valmin
        super(LabelCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td_contents(self, item, attr_list):
        """
        This is the contents of a status column to indicate whether a panel is live or has changes

        :param item:
        :param attr_list:
        :return:
        """
        if self.from_attr_list(item, attr_list):
            type = "success"
            status = "Live"
        else:
            type = "danger"
            status = "Changes"

        return '<p><span class="label label-{type}">{status}</span></p>'.format(type=type, status=status)

class ItemTablePanels(Table):
    args = {"style":"width:80px"}
    panelname = Col('Name')
    current_version = Col('Stable Version', column_html_attrs=args)
    view_panel = LinkCol('View Panel', 'panels.view_panel', url_kwargs=dict(id='panelid'), column_html_attrs=args)
    edit = LinkColEdit('Edit Panel', 'panels.edit_panel_process', url_kwargs=dict(id='panelid'), column_html_attrs=args)
    view = LinkCol('View Virtual Panels', 'panels.view_virtual_panels', url_kwargs=dict(id='panelid'), column_html_attrs=args)
    locked = LockCol('Locked', column_html_attrs=args)
    status = LabelCol('Status', column_html_attrs=args)
    make_live = LinkColLive('Make Live', 'panels.make_live', url_kwargs=dict(id='panelid'), column_html_attrs=args)
    # delete = LinkCol('Delete', 'delete_study', url_kwargs=dict(id='studyid'))


class ItemTableVPanels(Table):
    vp_name = Col('Name')
    current_version = Col('Stable Version')
    view_panel = LinkCol('View Panel', 'panels.view_vpanel', url_kwargs=dict(id='id'))
    edit = LinkColEdit('Edit Panel', 'panels.edit_virtual_panel_process', url_kwargs=dict(id='id'))
    locked = LockCol('Locked')
    status = LabelCol('Status')
    make_live = LinkColLive('Make Live', 'panels.make_virtualpanel_live', url_kwargs=dict(id='id'))
    # delete = LinkCol('Delete', 'delete_study', url_kwargs=dict(id='studyid'))


# TODO Are these needed? If so does redirect need to change?
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


class ItemTableLocked(Table):
    name = Col('Panel')
    username = Col('Locked By')
    toggle_lock = LinkCol('Toggle Lock', 'panels.toggle_locked', url_kwargs=dict(id='id'))


def isgene(s, gene):
    """
    Checks if a gene is in refflat

    :param s: db session token
    :type s: SQLAlchemy session
    :param gene: gene name
    :type gene: String
    :return: true or false
    :rtype: Boolean
    """
    test = s.query(Genes).filter(Genes.name.ilike(gene)).first()
    if test is None:
        return None
    else:
        return test.name


def check_panel_status(s, id):
    """
    Checks the status of a panel - i.e. whether it is live or  has uncommitted changes

    :param s: db session token
    :type s: SQLAlchemy session
    :param id: panel id
    :type id: Int
    :return: true - panel is live or false - panel has changes
    :rtype: Boolean
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
    Checks the status of a virtual panel - i.e. whether it is live or has uncommitted changes

    :param s: db session token
    :type s: SQLAlchemy session
    :param id: virtual panel id
    :type id: Int
    :return: true - panel is live or false - panel has changes
    :rtype: Boolean
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

@panels.route('/autocomplete', methods=['GET'])
def autocomplete():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Genes).filter(Genes.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    return jsonify(matching_results=data)


def create_design(regions):
    """
    Method to translate regions to the design file required for upload to Agilent.

    This file is in the format:

    *
    *
    *
    *

    and is comma separated instead of tab separated. All design files contain the +/- 25 bp extension

    :regions: merged sorted list of regions to be included in the BED file
    :type regions:
    :return: result string - fields are comma separated and lines are joined with a new line character
    :rtype: String
    """
    print(type(regions))
    result = []
    for i in regions:
        line = []
        line.append(i.chrom)
        line.append(str(i.start))
        line.append(str(i.end))
        line.append(i.name.replace(";", ","))
        result.append(line)

    design = '\n'.join(['\t'.join(l) for l in result])
    return design

def create_bed(regions):
    """
    Method to translate regions to BED file format.

    :return: result string - fields are comma separated and lines are joined with a new line character
    :rtype: String
    """
    result = []
    for i in regions:
        line = []
        line.append(i.chrom)
        line.append(str(i.start))
        line.append(str(i.end))
        line.append(i.name.replace(";", ","))
        result.append(line)

    bed = '\n'.join(['\t'.join(l) for l in result])
    return bed

@panels.route('/download')
@login_required
def download():
    """
    Allows the panel or virtual panel to be downloaded as a text file in the correct BED format using the name of
    the panel.

    The scope is defined as either panel or virtual to determine the query to be executed. The request can also specify
    the version of the panel to be downloaded.

    :return: Text file attachment to be downloaded
    :rtype: Flask Response Object
    """
    scope = request.args.get('scope')
    type = request.args.get('type')
    id = request.args.get('id')
    version = request.args.get('version')
    panel_name = request.args.get('name')

    if type == 'default':
        extension = 0
    else:
        extension = 25

    if scope == 'Panel':
        panel = get_regions_by_panelid(s, id, version, extension)
    elif scope == 'Virtual':
        panel = get_regions_by_vpanelid(s, id, version, extension)

    result = []

    for i in panel:
        line = []
        line.append(i.chrom)
        line.append(str(i.region_start))
        line.append(str(i.region_end))
        if not i.gene_name == '' and not i.gene_name == 'N/A':
            line.append(i.gene_name + ':' + i.name)
        else:
            line.append(i.name)
        result.append(line)

    bed = '\n'.join(['\t'.join(l) for l in result])

    bed_tool = BedTool(bed, from_string=True)
    bed_sorted = bed_tool.sort()
    bed_sorted_merged = bed_sorted.merge(c=4, o='collapse')

    if type == 'design':
        create_design(bed_sorted_merged)
        filename = "attachment; filename=" + panel_name + "_25bp_v" + version + "_" + current_user.id + "_" + time.strftime(
                         "%d-%m-%Y") + ".txt"
    else:
        create_bed(bed_sorted_merged)
        if type == "extension":
            filename = "attachment; filename=" + panel_name + "_25bp_v" + version + "_" + current_user.id + "_" + time.strftime(
                "%d-%m-%Y") + ".bed"
        else:
            filename = "attachment; filename=" + panel_name + "_v" + version + "_" + current_user.id + "_" + time.strftime(
                         "%d-%m-%Y") + ".bed"

    return Response(
        bed,
        mimetype='test/plain',
        headers={"Content-disposition": filename
                     }
    )




@panels.route('/panels', methods=['GET', 'POST'])
@login_required
# @lock_check
def view_panels(id=None):
    """
    Method to view panels, if project ID given then only return panels from that project.

    The Method also checks if each panel is locked (is being worked on by another user) and whether the user has
    permission to edit each panel, otherwise this action is not available to them.

    :param id: project id - this can be specified in the ajax request instead
    :type id: Int
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
        locked = check_if_locked(s, row["panelid"])
        row['permission'] = permission
        row['locked'] = locked

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
    """
    Method to view regions in a panel. If no panel ID is given, the method executes view_panels()

    The method checks the user has permission to edit the panel to determine whether this feature is available to them.
    It also checks if the panel is locked as this will also restrict access to the edit option.

    :return: If no ID given, redirects to "view_panels()", else renders template for panel view
    """
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
                # panel_name = i.panel_name
                current_version = i.current_version
        else:
            message = "This Panel has no regions yet & may also have changes that have not been made live"
            bed = 'disabled'
            current_version = version

        if check_user_has_permission(s, current_user.id, project_id):
            edit = ''
        else:
            edit = 'disabled'

        form = ViewPanel()
        v_list = range(1, current_version + 1)
        choices = []
        for i in v_list:
            choices.append((i, i))
        form.versions.choices = choices
        form.versions.default = version
        form.process()

        table = []

        for i in result:
            line = []
            line.append(i['chrom'])
            line.append(str(i['region_start']))
            line.append(str(i['region_end']))
            line.append(i['gene_name'])
            line.append(i['name'].replace(',', ' '))
            table.append(line)
        return render_template('panel_view.html', scope='Panel', table=json.dumps(table), panel=table,
                               panel_name=panel_name, edit=edit, bed=bed,
                               version=version, panel_id=id, project_id=project_id, message=message,
                               url=url_for('panels.view_panel'),
                               form=form)

    else:
        return redirect(url_for('panels.view_panels'))


@panels.route('/panels/wizard', methods=['GET', 'POST'])
@login_required
def create_panel_process():
    """
    Create panel wizard method.

    If request is "GET" method renders template for wizard
    If the request is "POST" method makes the panel live (if selected) and redirects to the view panel page

    :return: Rendered wizard template for "GET" request, redirect to view_panels() for "POST" request.
    """
    form = CreatePanelProcess()
    if request.method == "POST":
        make_live = request.form['make_live']
        panel_id = request.args.get('id')
        project_id = get_project_id_by_panel_id(s, panel_id)
        preftx_id = get_preftx_id_by_project_id(s, project_id)
        version = get_current_preftx_version(s, preftx_id)
        if not version:
            version = 0
        if make_live == "True":
            make_preftx_live(s, preftx_id, version + 1, current_user.id)
            make_panel_live(s, panel_id, 1, current_user.id)
        unlock_panel_query(s, panel_id)
        return redirect(url_for('panels.view_panel') + "?id=" + panel_id)
    elif request.method == "GET":
        return render_template('panel_createprocess.html', form=form, panel_id="main",
                               url=url_for('panels.create_panel_process'))


@panels.route('/panels/edit', methods=['GET', 'POST'])
@login_required
def edit_panel_process():
    """
    Edit panel wizard method.

    If the request method is "GET" the information for the panel is retrieved and the relevant HTML is created (e.g.
    gene buttons and tx drop downs. The template for the wizard is rendered and returned.
    If the request method is "POST" the panel and preferred tx are made live (if selected) and redirects to the
    view_panels() method.

    :return: if "GET" rendered wizard template is returned. If "POST" redirects to view_panels()
    """
    if request.method == "POST":
        make_live = request.form['make_live']
        panel_id = request.args.get('id')
        project_id = get_project_id_by_panel_id(s, panel_id)
        preftx_id = get_preftx_id_by_project_id(s, project_id)
        version = get_current_preftx_version(s, preftx_id)
        if not version:
            version = 0
        if make_live == "True":
            make_preftx_live(s, preftx_id, version + 1, current_user.id)
            make_panel_live(s, panel_id, 1, current_user.id)
        unlock_panel_query(s, panel_id)
        return redirect(url_for('panels.view_panel') + "?id=" + panel_id)
    elif request.method == "GET":
        panel_id = request.args.get('id')
        form = EditPanelProcess()
        panel_info = get_panel_info(s, panel_id)
        project_id = panel_info.project_id
        form.project.choices = [(project_id, panel_info.project_name), ]
        form.panelname.data = panel_info.name

        lock_panel(s, current_user.id, panel_id)

        genes = get_genes_by_panelid_edit(s, panel_id, panel_info.current_version)
        html = ""
        buttonlist = ""
        for gene in genes:
            gene_id = gene.id
            gene_name = gene.name
            preftx_id = get_preftx_by_gene_id
            upcoming_preftx = get_upcoming_preftx_by_gene_id(s, project_id, gene_id)
            all_tx = get_tx_by_gene_id(s, gene_id)

            gene_button = "<button name=\"genebutton\" type=\"button\" class=\"btn btn-success btn-md btngene\" data-name=\"" + \
                          gene_name + "\" data-id=\"" + str(
                gene_id) + "\"><span class='glyphicon glyphicon-ok'></span> " + \
                          gene_name + "</button> "
            buttonlist += gene_button
            tx_html = """<tr>
                            <td>
                                <label for=\"""" + gene_name + "\">" + gene_name + """</label>
                            </td>
                            <td>
                                <div class=\"form-group\">
                                <select class=\"form-control\" name=\"""" + gene_name + "\" id=\"" + gene_name + "\" disabled=\"disabled\">"

            for tx in all_tx:
                if upcoming_preftx == tx.id:

                    tx_html += "<option value=\"" + str(
                        tx.id) + "\" class=\"red\">" + tx.accession + " - This Is a Change Not Made Live Yet</option>" + \
                               """</select>
                                    </div>
                                       </td>
                               </tr>"""
                    break
                else:
                    tx_html += "<option value=\"" + str(tx.id) + "\""

                    if preftx_id == tx.id:
                        tx_html += " class=\"bolden\" selected"
                    else:
                        tx_html += " class=\"\""

                    tx_html += ">" + tx.accession + "</option>"
            tx_html += """</select>
                                </div>
                            </td>
                        </tr>"""
            html += tx_html

        return render_template('panel_createprocess.html', form=form, genes=html, genelist=buttonlist,
                               panel_id=panel_id,
                               url=url_for('panels.edit_panel_process') + "?id=" + panel_id)


@panels.route('/panels/add', methods=['POST'])
@login_required
def add_panel():
    """
    Method to add panel to db.

    Uses panel name and project ID to create a panel in the db and returns the unique ID for the panel

    :return: panel id (in JSON format)
    """
    panel_name = request.json['panel_name']
    project_id = request.json['project_id']
    panel_id = create_panel_query(s, project_id, panel_name, current_user.id)
    return jsonify(panel_id)


@panels.route('/panels/remove', methods=['POST'])
@login_required
def remove_panel():
    """
    Method to delete panel from db

    If the panel has not been made live it can be removed from the db.

    :return: status (in JSON format)
    """
    panel_name = request.json['panel_name']
    remove_panel_query(s, panel_name)
    return jsonify('complete')


@panels.route('/panels/upload', methods=['POST'])
@login_required
def upload_multiple():
    """
    Method to allow a file of gene names to be uploaded for a panel.

    The file is read in the javascript at the client side and a list of gene names are sent to the method within the
    ajax.
    The create_panel_get_tx() method is applied to each gene in the list and teh html is combined before being returned
    to the client side for display.

    :return: JSON containing HTML for the transcripts table and the gene button list as ewll as for the messages to be
    displayed on the initial screen.
    """
    gene_list = request.json['gene_list']
    project_id = request.json['project_id']
    all_message = ''
    html = ''
    added_list = []
    button_list = ''

    for gene in sorted(gene_list):
        if gene == "" or gene in added_list:
            continue
        dct = create_panel_get_tx(gene, project_id)
        if dct["message"] == "added":
            added_list.append(gene)
        else:
            all_message += dct["message"]
        try:
            html += dct["html"]
        except KeyError:
            pass
        try:
            button_list += dct["button_list"]
        except KeyError:
            pass

    added_message = "<div class =\"alert alert-success\" name=\"message-fade\"><strong>Just so you know... </strong> "

    for g in added_list:
        if added_list.index(g) == len(added_list) - 1:
            string = "and " + g
            added_message += string
        else:
            string = g + ", "
            added_message += string

    if added_message != "<div class =\"alert alert-success\" name=\"message-fade\"><strong>Just so you know... </strong> ":
        added_message += " have been added</div>"
        all_message += added_message
    return jsonify({'message': all_message, 'html': html, 'button_list': button_list})


@panels.route('/panels/preftx', methods=['POST'])
@login_required
def create_panel_get_tx(gene_name=None, project_id=None):
    """
    Method to produce HTML for create panel wizard when new gene is added.

    Each gene is checked against the database before the HTML is generated for the transcript list and gene button list
    within the process workflow. The method checks for changes in the preferred transcript that have yet to be applied
    so these changes are displayed correctly.

    The method can either be accessed through an AJAX query from the client side or within the views (from multiple
    upload). If JSON is specified, the method returns the complete HTML sections using jsonify.

    :param gene_name: Name of gene to be checked and added
    :type gene_name: String
    :param project_id: Unique ID for project
    :type project_id: Int
    :return: Dictionary of HTML sections to be added to web page (warning/info messages, tx rows, gene buttons)
    """
    json = False
    if not gene_name:
        gene_name = request.json['gene_name']
        project_id = request.json['project_id']
        json = True
    exists = isgene(s, gene_name)
    if exists:
        gene_name = exists
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

        gene_button = "<button name=\"genebutton\" type=\"button\" class=\"btn btn-danger btn-md btngene\" data-name=\"" + \
                      gene_name + "\" data-id=\"" + str(
            gene_id) + "\"><span class='glyphicon glyphicon-pencil'></span> " + \
                      gene_name + "</button> "

        for tx in all_tx:
            if upcoming_preftx == tx.id:

                html = """<tr>
                    <td>
                        <label for=\"""" + gene_name + "\">" + gene_name + """</label>
                    </td>
                    <td>
                        <div class=\"form-group\">
                        <select class=\"form-control\" name=\"""" + gene_name + "\" id=\"" + gene_name + "\">" + \
                       "<option value=\"" + str(
                    tx.id) + "\" class=\"red\">" + tx.accession + " - This Is a Change Not Made Live Yet</option>" + \
                       """</select>
                            </div>
                               </td>
                       </tr>"""

                success_message = "<div class =\"alert alert-success\" name=\"message-fade\"><strong>Just so you know... </strong> " + gene_name + " was added</div>"
                if json:
                    return jsonify({'html': html, 'button_list': gene_button, 'message': success_message})
                else:
                    return {'html': html, 'button_list': gene_button, 'message': "added"}
            else:
                html += "<option value=\"" + str(tx.id) + "\""

                if preftx_id == tx.id:
                    html += " class=\"bolden\" selected"
                else:
                    html += " class=\"\""

            html += ">" + tx.accession + "</option>"
        html += """</select>
                    </div>
                </td>
            </tr>"""

        success_message = "<div class =\"alert alert-success\" name=\"message-fade\"><strong>Just so you know... </strong> " + gene_name + " was added</div>"

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
    Creates a custom region from ajax query and adds region to versions table for specified panel.

    Method checks that region does not exist before adding to the database

    :return:
    """
    panel_id = request.json["panel_id"]
    chrom = request.json["chrom"]
    start = request.json["start"]
    end = request.json["end"]
    name = request.json["name"]
    regions = select_region_by_location(s, chrom, start, end)  # if region already exists, return current entry
    if regions:
        for i in regions:
            add_region_to_panel(s, i.id, panel_id)
            s.commit()
            continue
    else:
        create_custom_region(s, panel_id, chrom, start, end, name)

    return jsonify("complete")


@panels.route('/panels/add-all-regions', methods=['POST'])
@login_required
def add_all_regions():
    """
    Method to add all regions for a gene to versions table

    :return: Dictionary containing gene id
    """
    gene_id = request.json['gene_id']
    panel_id = request.json['panel_id']
    add_genes_to_panel_with_ext(s, panel_id, gene_id)
    return jsonify({"genes": [gene_id,]})

@panels.route('/panels/add_regions', methods=['POST'])
@login_required
def add_panel_regions():
    """
    Method to add selected regions and relevant extensions to a panel.

    When regions for a gene are added to a panel the preferred tx is also added/updated. The regions are sent within a
    dictionary containing the containing the region ID and both extensions (zero if no ext to be added).

    :return: Jsonify string
    """
    version_ids = request.json['id_ext']
    panel_id = request.json['panel_id']
    tx_id = request.json['pref_tx_id']
    project_id = request.json['project_id']
    gene_name = request.json['gene_name']

    add_preftxs_to_panel(s, project_id, [{"gene": gene_name, "tx_id": tx_id}, ])

    for i in version_ids:
        if i["ext_5"] == 0:
            ext_5 = None
        else:
            ext_5 = i["ext_5"]

        if i["ext_3"] == 0:
            ext_3 = None
        else:
            ext_3 = i["ext_3"]
        add_region_to_panel(s, i["id"], panel_id, ext_3=ext_3, ext_5=ext_5)
    s.commit()
    return jsonify("complete")


@panels.route('/panels/update_ext', methods=['POST'])
@login_required
def update_ext():
    """
    Method to update the extension for a region.

    :return:
    """
    panel_id = request.json['panel_id']
    region_id = request.json['region_id']
    e3 = request.json["ext_3"]
    e5 = request.json["ext_5"]

    current_version = get_current_version(s, panel_id)
    version = get_version_row(s, panel_id, region_id, current_version)
    version_id = version[0]
    intro = version[1]

    if e3 is not None:
        ext_3 = e3
    else:
        ext_3 = version[3]
    if e5 is not None:
        ext_5 = e5
    else:
        ext_5 = version[4]
    if int(intro) > int(current_version):
        update_ext_query(s, version_id, ext_3=ext_3, ext_5=ext_5)
    else:
        update_ext_query(s, version_id, panel_id=panel_id, ext_3=ext_3, ext_5=ext_5, current_version=current_version,
                         region_id=region_id)

    return jsonify("complete")


@panels.route('/panels/remove_regions', methods=['POST'])
@login_required
def remove_panel_regions():
    """
    Method to remove regions from a panel.

    The query associated with this method checks whether the region was live in the panel. If it has been in a live
    version the region remains in the versions table and the "last" field is populated with the current version.
    If the region has never been included in a live version of the panel, it is removed from the table.

    The method returns the number of regions in the panel. If this is zero, locks will be put in place within the
    wizard as the panel cannot be made live etc.

    :return: number of regions in the panel using jsonify
    """
    if type(request.json['ids']) is list:
        version_ids = request.json['ids']
    else:
        version_ids = request.json['ids'].replace('[', '').replace(']', '').split(',')
    # TODO does this happen?
    if type(version_ids) is str:
        version_ids = version_ids.split(',')
    panel_id = request.json['panel_id']

    for i in version_ids:
        remove_version_from_panel(s, int(panel_id), int(i))

    panel = get_panel_by_id(s, panel_id)  # check if there are still regions in the panel
    length = len(list(panel))
    return jsonify(length)


@panels.route('/live', methods=['GET', 'POST'])
@login_required
def make_live():
    """
    Method to make a panel live given a panel ID

    :return: redirection to view panels
    """
    panelid = request.args.get('id')
    locked = check_if_locked(s, panelid)
    if locked:
        unlock_panel_query(s, panelid)
    current_version = get_current_version(s, panelid)
    if not current_version:
        current_version = 0
    new_version = current_version + 1
    make_panel_live(s, panelid, new_version, current_user.id)
    return redirect(url_for('panels.view_panels'))


@panels.route('/unlock', methods=['GET', 'POST'])
@login_required
def unlock_panel():
    """
    Method to unlock a panel so it can be edited by others

    :return: redirection to view panels
    """
    panelid = request.args.get('panelid')
    unlock_panel_query(s, panelid)

    return redirect(url_for('panels.view_panels'))


# TODO Are these methods needed?
# @panels.route('/edit')
# @login_required
# def edit_panel_page(panel_id=None):
#     """
#
#
#     :param panel_id: ID for panel to be edited. This can be none
#     :return:
#     """
#     id = request.args.get('panelid')
#     lock_panel(s, current_user.id, id)
#     if id is None:
#         id = panel_id
#     panel_info = s.query(Panels, Projects).join(Projects).filter(Panels.id == id).values(
#         Panels.current_version,
#         Panels.name,
#         Panels.locked
#     )
#     for i in panel_info:
#         version = i.current_version
#         name = i.name
#     panel = get_panel_edit(s, id=id, version=version)
#     form = RemoveGene(panelId=id)
#     add_form = AddGene(panelIdAdd=id)
#
#     result = []
#     genes = []
#     for i in panel:
#         row = dict(zip(i.keys(), i))
#         row['original_start'] = row["start"]
#         row['original_end'] = row["end"]
#         if row["intro"] > row["current_version"]:
#             row["status"] = False
#         else:
#             row["status"] = True
#         result.append(row)
#         if row["extension_5"]:
#             row["start"] = int(row["start"]) + int(row["extension_5"])
#         if row["extension_3"]:
#             row["end"] = int(row["end"]) + int(row["extension_3"])
#         genes.append(Markup("<button type=\"button\" class=\"btn btn-danger btn-md btngene\" data-id=\"" + str(
#             i.panelid) + "\" data-name=\"" + i.genename + "\" data-toggle=\"modal\" data-target=\"#removeGene\" id=\"myDeleteButton\"><span class=\"glyphicon glyphicon-remove\"></span> " + i.genename + "</button>"))
#     table = ItemTablePanel(result, classes=['table', 'table-striped'])
#     return render_template('panel_edit.html', panel_name=name, version=version,
#                            panel_detail=table, genes=" ".join(sorted(set(genes))), form=form, add_form=add_form,
#                            panel_id=id)
#
#
# @panels.route('/edit', methods=['POST', 'GET'])
# @login_required
# def edit_panel():
#     if request.method == 'POST':
#         panel_id = request.form["panel_id"]
#         for v in request.form:
#             if v.startswith("region"):
#                 value = int(request.form[v])
#                 region, region_id, intro, last, current_version, id, start, ext_5, end, ext_3, scope = v.split("_")
#                 if ext_5:
#                     original_start = int(start) + int(ext_5)
#                 else:
#                     original_start = start
#                 if ext_3:
#                     original_end = int(end) + int(ext_3)
#                 else:
#                     original_end = end
#                 if scope == "start":
#
#                     if value != int(original_start):
#
#                         extension_5 = int(value) - int(original_start)
#                         check = s.query(Versions).filter_by(region_id=region_id,
#                                                             intro=int(current_version) + 1).count()
#
#                         if check > 0:
#                             s.query(Versions).filter_by(region_id=region_id,
#                                                         intro=int(current_version) + 1).update(
#                                 {Versions.extension_5: extension_5})
#                             s.commit()
#                         else:
#                             s.query(Versions).filter_by(id=id).update({Versions.last: current_version})
#                             s.commit()
#                             v = Versions(intro=int(current_version) + 1, last=None, panel_id=int(panel_id),
#                                          comment=None,
#                                          extension_3=None, extension_5=int(extension_5),
#                                          region_id=int(region_id))
#                             s.add(v)
#                             s.commit()
#                 if scope == "end":
#                     if value != int(original_end):
#                         extension_3 = int(value) - int(original_end)
#
#                         check = s.query(Versions).filter_by(region_id=region_id,
#                                                             intro=int(current_version) + 1).count()
#                         if check > 0:
#                             s.query(Versions).filter_by(region_id=region_id,
#                                                         intro=int(current_version) + 1).update(
#                                 {Versions.extension_3: extension_3})
#                             s.commit()
#                         else:
#                             s.query(Versions).filter_by(id=id).update({Versions.last: current_version})
#                             s.commit()
#                             v = Versions(intro=int(current_version) + 1, last=None, panel_id=int(panel_id),
#                                          comment=None,
#                                          extension_3=extension_3, extension_5=None,
#                                          region_id=int(region_id))
#                             s.add(v)
#                             s.commit()
#     return edit_panel_page(panel_id=panel_id)
#
#
# @panels.route('/delete/gene', methods=['POST'])
# @login_required
# def remove_gene():
#     # s = scoped_session(db.session)
#     form = RemoveGene()
#     if request.method == 'POST':
#         id = form.data['panelId']
#         gene = form.data['geneName']
#         panel_info = get_panel_edit(s, id, 1)
#         ids = []
#         for i in panel_info:
#             if i.genename == gene:
#                 # todo add if in here - if the gene is not already in a live panel it is okay to delete completely
#                 s.query(Versions).filter_by(id=i.id).update({Versions.last: i.current_version})
#                 ids.append(i.id)
#     s.commit()
#     return edit_panel_page(id)
#
#
# @panels.route('/delete/gene', methods=['POST'])
# @login_required
# def delete_region():
#     pass
#     return edit_panel_page(id)
#
#
# @panels.route('/delete/add', methods=['POST'])
# @login_required
# def add_gene():
#     """
#     adds a gene to a panel
#     :return: edit panel page
#     """
#     form = AddGene()
#     if request.method == 'POST':
#         id = form.data['panelIdAdd']
#         gene = form.data['genes']
#         if isgene(s, gene):
#             add_genes_to_panel(s, id, gene)
#     return edit_panel_page(id)


#################
# VIRTUAL PANELS
################

@panels.route('/virtualpanels', methods=['GET', 'POST'])
@login_required
def view_virtual_panels(id=None):
    """
   Method to view virtual panels, if panel ID given then only return virtual panels from that panel

   :param id: panel id
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

        row["current_version"] = round(row["current_version"], 1)

        status = check_virtualpanel_status(s, row["id"])
        row["status"] = status
        permission = check_user_has_permission(s, current_user.id, row["projectid"])
        locked = check_if_locked_by_user_vpanel(s, current_user.id, row["panelid"])

        row['permission'] = permission
        row['locked'] = locked

        status = check_virtualpanel_status(s, row["id"])
        row["status"] = status

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
    """
    Method to view the regions in a virtual panel.

    The method checks permissions to determine if edit etc is available.

    :return:
    """
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
                version = panel_details.current_version
            panel_name = panel_details.name
            project_id = panel_details.project_id
        panel = get_regions_by_vpanelid(s, id, version)
        result = []
        rows = list(panel)
        if len(rows) != 0:
            bed = ''
            for i in rows:
                row = dict(zip(i.keys(), i))
                result.append(row)
                panel_name = i.panel_name
                current_version = i.current_version
        else:
            message = "This Panel has no regions yet & may also have changes that have not been made live yet"
            bed = 'disabled'
            current_version = version
        print(type(version))
        current_version = round(current_version, 1)
        version = round(float(version), 1)

        if check_user_has_permission(s, current_user.id, project_id):
            edit = ''
        else:
            edit = 'disabled'

        form = ViewPanel()
        v_list = get_prev_versions_vp(s, id)
        choices = []
        for i in v_list:
            choices.append((i, i))

        if (current_version, current_version) not in choices:
            choices.append((current_version, current_version))

        form.versions.choices = choices
        form.versions.default = current_version
        form.process()

        table = []

        for i in result:
            line = []
            line.append(i['chrom'])
            line.append(str(i['region_start']))
            line.append(str(i['region_end']))
            line.append(i['gene_name'])
            line.append(i['name'].replace(',', ' '))
            table.append(line)

        return render_template('panel_view.html', table=json.dumps(table), panel=table, panel_name=panel_name,
                               edit=edit, bed=bed,
                               version=version, panel_id=id, message=message, url=url_for('panels.view_vpanel'),
                               scope='Virtual', form=form)

    else:
        return redirect(url_for('panels.view_virtual_panels'))


@panels.route('/virtualpanels/wizard', methods=['GET', 'POST'])
@login_required
def create_virtual_panel_process():
    """
    Method for create virtual panel wizard.

    If request is "GET" method renders virtual panel process html.
    If request if "POST" the method checks if the virtual panel is to be made live and unlocks the panel for future
    editing.

    :return: "GET" returns rendered template for wizard, "POST" redirects to view virtual panel
    """
    form = CreateVirtualPanelProcess()

    if request.method == "POST":
        make_live = request.form['make_live']
        vp_id = request.args.get('id')
        if make_live == "True":
            panel_id = get_panel_by_vp_id(s, vp_id)
            make_vp_panel_live(s, vp_id)
        panel_id = get_panel_by_vp_id(s, vp_id)
        unlock_panel_query(s, panel_id)
        return redirect(url_for('panels.view_vpanel') + "?id=" + vp_id)
    elif request.method == "GET":
        url = url_for('panels.create_virtual_panel_process')
        return render_template('virtualpanels_createprocess.html', form=form, url=url, vp_id="main")


@panels.route('/virtualpanels/edit', methods=['GET', 'POST'])
@login_required
def edit_virtual_panel_process():
    """
    Method for edit virtual panel wizard.

    If request is "GET" the method locks the panel so it cannot be edited by any other user. It then retrieves all
    information about the current panel and virtual panel. The query associated with this method gets the virtual panel
    information with respect to the future version number so changes that have already been added to the virtual panel
    can also be viewed.

    If request is "POST" the method checks if the panel should be made live and unlocks the panel for editing. The
    method then redirects to the view virtual panel page.

    :return: If "GET" the method returns a rendered template for the edit wizard. If "POST" the method redirects to
    the view panel page.
    """
    form = EditVirtualPanelProcess()

    vp_id = request.args.get('id')
    panel_id = get_panel_by_vp_id(s, vp_id)
    if request.method == "POST":
        if request.form['make_live'] == "True":
            make_vp_panel_live(s, vp_id)
        unlock_panel_query(s, panel_id)
        return redirect(url_for('panels.view_vpanel') + "?id=" + vp_id)
    elif request.method == "GET":
        lock_panel(s, current_user.id, panel_id)
        panel_info = get_panel_details_by_id(s, panel_id)
        panel_name = ""
        for i in panel_info:
            panel_name = i.name
        form.panel.choices = [(panel_id, panel_name), ]

        panel_version = get_current_version(s, panel_id)
        panel_genes = get_genes_by_panelid(s, panel_id, panel_version)
        vp_info = get_vpanel_details_by_id(s, vp_id)
        vp_version = vp_info.current_version
        vp_name = vp_info.name
        form.vpanelname.data = vp_name
        vp_genes = get_genes_by_vpanelid_edit(s, vp_id, vp_version)
        gene_html = """<li class=\"list-group-item list-group-item-select-all\"><strong>Select all</strong> 
                    <div class=\"material-switch pull-right\">
                        <input type=\"checkbox\" id=\"all-genes\">
                        <label for=\"all-genes\" class=\"label-success\"></label>
                    </div>
                </li>"""
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
                button = "<button name=\"genebutton\" type=\"button\" class=\"btn btn-success btn-md btngene\" data-name=\"" + \
                         i.name + "\" data-id=\"" + str(i.id) + "\"><span class='glyphicon glyphicon-ok'></span> " + \
                         i.name + "</button> "
                genelist += button

            else:
                line = "<li class=\"list-group-item\">" + \
                       i.name + \
                       "<div class=\"material-switch pull-right\"><input type=\"checkbox\" name=\"" + str(i.id) + \
                       "\" id=\"" + i.name + "\"><label for=\"" + i.name + \
                       "\" class=\"label-success label-gene\"></label></div></li>"
            gene_html += line

        url = url_for('panels.edit_virtual_panel_process') + '?id=' + str(vp_id)
        return render_template('virtualpanels_createprocess.html', form=form, genes=gene_html, genelist=genelist,
                               vp_id=vp_id, panel_name=vp_name, current_version=vp_version, url=url)


@panels.route('/virtualpanels/add', methods=['POST'])
@login_required
def add_vp():
    """
    Method to add virtual panel to DB.

    :return: jsonify ID of virtual panel
    """
    vp_name = request.json['vp_name']
    panel_id = request.json['panel_id']
    vp_id = create_virtualpanel_query(s, vp_name, panel_id)
    if vp_id != -1:
        lock_panel(s, current_user.id, panel_id)
    return jsonify(vp_id)


@panels.route('/virtualpanels/remove', methods=['POST'])
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

    html = """<li class=\"list-group-item list-group-item-select-all\"><strong>Select all</strong> 
                    <div class=\"material-switch pull-right\">
                        <input type=\"checkbox\" id=\"all-genes\">
                        <label for=\"all-genes\" class=\"label-success\"></label>
                    </div>
                </li>"""
    for gene in genes:
        line = "<li class=\"list-group-item\">" + \
               gene.name + \
               "<div class=\"material-switch pull-right\"><input type=\"checkbox\" name=\"" + str(
            gene.id) + "\" id=\"" + \
               gene.name + "\"><label for=\"" + gene.name + "\" class=\"label-success label-gene\"></label></div></li>"
        html += line
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
                            </li>"""

    if not vpanel_id:
        html += "<li><button type=\"button\" class=\"btn btn-primary\" id=\"create-regions\" name=\"Create\">Create Custom Region</button></li>"

    html += """</ul>

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
            current_regions.append(i.region_id)
            v_id = str(i.region_id)
        else:
            v_id = str(i.version_id)

        row = """<tr>
                        <td><label for=\"""" + v_id + "\">" + v_id + "</label></td>" + \
              "<td>" + i.chrom + "</td>" + \
              "<td>" + str(i.region_start) + "</td>" + \
              "<td>" + str(i.region_end) + "</td>" + \
              "<td>" + i.name.replace(',', '\n') + "</td>" + \
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
    return jsonify({'html': html, 'ids': current_regions})

@panels.route('/virtualpanels/getregions', methods=['POST'])
def select_vp_regions(gene_id, gene_name, panel_id):
    """

    :param gene_id:
    :param gene_name:
    :param panel_id:
    :return:
    """
    regions = get_panel_regions_by_geneid(s, gene_id, panel_id)
    html = "<h3 name=\"" + gene_id + "\">" + gene_name + "</h3><ul class=\"list-unstyled list-inline pull-right\">" + \
           """<li>
               <button type=\"button\" class=\"btn btn-success\" id=\"add-regions\" name=\"""" + gene_name + """\" disabled=\"disabled\">Add Regions</button>
                        </li>
                        <li>
                            <button type=\"button\" class=\"btn btn-danger\" id=\"remove-gene\" name=\"""" + gene_name + """\">Remove Gene</button>
                        </li>
                    </ul>

                <table class=\"table table-striped\" id=\"region-table\">
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
        v_id = str(i.version_id)
        coord = "<td>" + str(i.region_start) + "</td>" + \
                "<td>" + str(i.region_end) + "</td>"
        row = """<tr>
                            <td><label for=\"""" + v_id + "\">" + v_id + "</label></td>" + \
              "<td>" + i.chrom + "</td>" + coord + \
              "<td>" + i.name.replace(',', '\n') + "</td>" + \
              """<td><div class=\"material-switch pull-right\">
                      <input type=\"checkbox\" id=\"""" + v_id + """\" name=\"region-check\">
                                    <label for=\"""" + v_id + """\" class=\"label-success label-region\" ></label>
                                </div></td>
                        </tr>"""
        html += row

    html += "</table>"

    return html


@panels.route('/panels/getregions', methods=['POST'])
def select_regions(gene_id=None, gene_name=None, panel_id=None, added=False, utr=False):
    """

    :return:
    """
    changed_regions = {}
    include_utr = False
    if added: #added is true when the gene has been added to the panel during the edit (no regions have been saved to versions yet)
        if not utr:  # if utr is false (default) then only coding regions are added
            regions = get_regions_by_gene_no_utr(s, gene_id)
        else:
            regions = get_regions_by_geneid(s, gene_id)
    else:
        if utr is None:
            include_utr = check_if_utr(s, gene_id, panel_id)
            if include_utr:
                regions = get_regions_by_geneid_with_versions(s, gene_id, panel_id)
            else:
                regions = get_regions_by_geneid_with_versions_no_utr(s, gene_id, panel_id)
        elif not utr:
            regions = get_regions_by_geneid_with_versions_no_utr(s, gene_id, panel_id)
            changed_regions = get_altered_region_ids_exclude(s, gene_id, panel_id)
        else:
            regions = get_regions_by_geneid_with_versions(s, gene_id, panel_id)
            changed_regions = get_altered_region_ids_include(s, gene_id, panel_id)
    if utr or include_utr:
        ok_opac = "1"
        ok_active = "btn-success active"
        remove_opac = "0"
        remove_active = "btn-default"
    else:
        ok_opac = "0"
        ok_active = "btn-default"
        remove_opac = "1"
        remove_active = "btn-danger active"

    utr_html = """<li>
                        <div class="btn-group" role="group" aria-label="basic label">
                            <p style="text-align: center; vertical-align: middle; display: table-cell;">Include UTR </p>
                        </div>

                        <div class="btn-group btn-group-xs" role="group" aria-label="...">
                            <a id="btnOn" href="javascript:;" class="btn """ +  ok_active + """""><span class="glyphicon glyphicon-ok" style="opacity: """ + ok_opac + """;"></span></a>
                            <a id="btnOff" href="javascript:;" class="btn """ + remove_active + """""><span class="glyphicon glyphicon-remove" style="opacity: """ + remove_opac + """;"></span></a>
                        </div>
                        <input type="radio" name="menucolor" value="navbar-default" checked>
                        <input type="radio" name="menucolor" value="navbar-inverse">
                </li>"""

    html = "<h3 name=\"" + gene_id + "\">" + gene_name + "</h3><ul class=\"list-unstyled list-inline pull-right\">" + \
           utr_html + \
           """<li>
               <button type=\"button\" class=\"btn btn-success\" id=\"add-regions\" name=\"""" + gene_name + """\" disabled=\"disabled\">Add Regions</button>
                    </li>
                    <li>
                        <button type=\"button\" class=\"btn btn-danger\" id=\"remove-gene\" name=\"""" + gene_name + """\">Remove Gene</button>
                    </li>
                </ul>

            <table class=\"table table-striped\" id=\"region-table\">
                <thead>
                    <tr>
                        <th width='14%'>ID</th>
                        <th width='13%'>Chrom</th>
                        <th width='17%'>Region Start</th>
                        <th width='17%'>Region End</th>
                        <th width='22%'>Names</th>
                        <th width='17%'>Select All <div class="material-switch pull-right">
                                            <input type="checkbox" id="checkAll">
                                            <label for="checkAll" class="label-success label-selectall"></label>
                                        </div>
                        </th>
                    </tr>
                </thead>"""

    store = {}
    for i in regions:
        v_id = str(i.region_id)
        if i.region_id in changed_regions.keys():
            h = """<div class=\"material-switch pull-right\">
                                <input type=\"checkbox\" id=\"""" + v_id + """\" name=\"region-check\">
                                <label for=\"""" + v_id + """\" class=\"label-success label-region\" checked=\"checked\"></label>
                            </div>"""
            if changed_regions[i.region_id]['position'] == 'both':
                start = str(changed_regions[i.region_id]['coord'][0])
                start_style = "style=\"color:red;\" "
                end = str(changed_regions[i.region_id]['coord'][1])
                end_style = "style=\"color:red;\" "
                end_column = """<div class=\"material-switch pull-right\">
                                                <input type=\"checkbox\" id=\"""" + v_id + """\" name=\"region-check\">
                                                <label for=\"""" + v_id + """\" class=\"label-success label-region\" ></label>
                                            </div>"""
            elif changed_regions[i.region_id]['position'] == 'start':
                store[i.region_id] = {"start":{'html':h, 'value':i.region_start}}
                start = str(changed_regions[i.region_id]['coord'])
                start_style = "style=\"color:red;\" "
                end = str(i.region_end + i.ext_3)
                end_style = ""
                end_column = """<ul class="list-unstyled list-inline pull-right" name="edit_region">
                                                <li>
                                                    <button type="button" class="btn btn-small btn-success" name="update" data-name="region_start">
                                                        <span class="glyphicon glyphicon-floppy-disk"></span>
                                                    </button>
                                                </li>
                                                <li>
                                                    <button type="button" class="btn btn-small btn-danger" name="undo">
                                                        <span class="glyphicon glyphicon-remove" name="undo"></span>
                                                    </button>
                                                </li>
                                            </ul>"""
            else:
                store[i.region_id] = {"end": {'html': h, 'value': i.region_end}}
                start = str(i.region_start - i.ext_5)
                start_style = ""
                end = str(changed_regions[i.region_id]['coord'])
                end_style = "style=\"color:red;\" "
                end_column = """<ul class="list-unstyled list-inline pull-right" name="edit_region">
                                <li>
                                    <button type="button" class="btn btn-small btn-success" name="update" data-name="region_end">
                                        <span class="glyphicon glyphicon-floppy-disk"></span>
                                    </button>
                                </li>
                                <li>
                                    <button type="button" class="btn btn-small btn-danger" name="undo">
                                        <span class="glyphicon glyphicon-remove" name="undo"></span>
                                    </button>
                                </li>
                            </ul>"""
        else:
            start = str(i.region_start - i.ext_5)
            start_style = ""
            end = str(i.region_end + i.ext_3)
            end_style = ""
            end_column = """<div class=\"material-switch pull-right\">
                                <input type=\"checkbox\" id=\"""" + v_id + """\" name=\"region-check\">
                                <label for=\"""" + v_id + """\" class=\"label-success label-region\" ></label>
                            </div>"""

        coord = "<td><input " + start_style + "class=\"form-control\" id=\"" + str(
            i.region_start) + "\" name=\"region_start\" type=\"text\" value=\"" + start + "\"></td>" + \
                "<td><input " + end_style + "class=\"form-control\" id=\"" + str(
            i.region_end) + "\" name=\"region_end\" type=\"text\" value=\"" + end + "\"></td>"

        row = """<tr>
                    <td><label for=\"""" + v_id + "\">" + v_id + "</label></td>" + \
              "<td>" + i.chrom + "</td>" + coord + \
              "<td class=\"expand\">" + i.name.replace(',', '\n') + "</td>" + \
              "<td>" + end_column + "</td></tr>"
        html += row

    html += "</table>"
    return html, store


@panels.route('/virtualpanels/editregions', methods=['POST'])
def edit_vp_regions():
    """

    :return:
    """
    gene_id = request.json['gene_id']
    gene_name = request.json['gene_name']
    panel_id = request.json['panel_id']
    vpanel_id = request.json['vpanel_id']
    utr = request.json['include_utr']

    html = ""
    if vpanel_id:
        html = select_vp_regions(gene_id, gene_name, panel_id)
        regions = get_vprelationships(s, vpanel_id, gene_id)
    else:
        regions = get_versions(s, panel_id, gene_id)

    version_ids = []
    for i in regions:
        version_ids.append(i[0])
    store = {}
    if len(version_ids) > 0:
        html = html.replace("Add Regions", "Update Regions")

    if not vpanel_id and len(version_ids) > 0:
        if not utr:
            html, store = select_regions(gene_id=gene_id, gene_name=gene_name, panel_id=panel_id)
        elif utr == "added":
            html, store = select_regions(gene_id=gene_id, gene_name=gene_name, panel_id=panel_id, utr=None)
        else:
            html, store = select_regions(gene_id=gene_id, gene_name=gene_name, panel_id=panel_id, utr=True)

    elif not vpanel_id:
        if not utr:
            html, store = select_regions(gene_id=gene_id, gene_name=gene_name, panel_id=panel_id, added=True)
        else:
            html, store = select_regions(gene_id=gene_id, gene_name=gene_name, panel_id=panel_id, added=True, utr=True)
    d = {'html': html, 'ids': version_ids, 'store':store}
    return jsonify(d)


@panels.route('/virtualpanels/add_regions', methods=['POST'])
@login_required
def add_vp_regions():
    version_ids = request.json['ids']
    vpanel_id = request.json['vp_id']
    for i in version_ids:
        add_version_to_vp(s, vpanel_id, i)
    s.commit()
    return jsonify("complete")

@panels.route('/virtualpanels/add-all-regions', methods=['POST'])
@login_required
def add_all_regions_vp():
    """
    Method to add all regions for a gene to versions table

    :return: Dictionary containing gene id
    """
    gene_id = request.json['gene_id']
    vpanel_id = request.json['vpanel_id']
    panel_id = request.json['panel_id']
    add_all_regions_to_vp(s,panel_id,gene_id,vpanel_id)
    return jsonify({"genes": [gene_id,]})

@panels.route('/virtualpanels/remove_regions', methods=['POST'])
@login_required
def remove_vp_regions():
    """

    :return:
    """
    version_ids = request.json['ids']
    if type(version_ids) != list:
        version_ids = version_ids.replace('[', '').replace(']', '').split(',')
    vpanel_id = request.json['vp_id']
    for i in version_ids:
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
    vpanelid = request.args.get('id')
    panelid = get_panel_by_vp_id(s, vpanelid)
    locked = check_if_locked(s, panelid)
    if locked:
        if current_user.id == get_locked_user(s, panelid):
            make_vp_panel_live(s, vpanelid)
        return redirect(url_for('panels.view_virtual_panels'))
    else:
        make_vp_panel_live(s, vpanelid)
        return redirect(url_for('panels.view_virtual_panels'))


@panels.route('/virtualpanels/delete', methods=['GET', 'POST'])
def delete_virtualpanel():
    """


    :return:
    """
    u = db.session.query(VirtualPanels).filter_by(id=request.args.get('id')).first()
    db.session.delete(u)
    db.session.commit()
    return view_virtual_panels()


@panels.route('/locked', methods=['GET', 'POST'])
@login_required
def manage_locked(message=None):
    """
    view locked panels

    :param message: message to display
    :return: rendered html template
    """
    locked = get_all_locked_by_username(s, current_user.id)
    result = []
    for i in locked:
        row = dict(zip(i.keys(), i))
        result.append(row)
    table = ItemTableLocked(result, classes=['table', 'table-striped'])
    return render_template('locked.html', table=table, message=message)


@panels.route('/locked/toggle/panel', methods=['GET', 'POST'])
@login_required
def toggle_locked():
    """
    toggles the locked status of a panel
    useful if someone has forgotten they have left a panel locked - an admin can unlock

    :return: view_locked method
    """
    panel_id = request.args.get('id')
    json  = False
    if not panel_id:
        json = True
        panel_id = request.json['id']
    project_id = get_project_id_by_panel_id(s, panel_id)
    if current_user.id == get_locked_user(s, panel_id) and json:
        unlock_panel_query(s, panel_id)
        return jsonify("complete")
    elif check_user_has_permission(s, current_user.id, project_id):
        unlock_panel_query(s, panel_id)
        return manage_locked(message="Panel Unlocked")
    else:
        return manage_locked(message="Hmmmm you don't have permission to do that")



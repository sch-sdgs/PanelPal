from app.queries import *
from sqlalchemy import and_, or_

from app.views import message
from app.mod_admin.queries import get_user_id_by_username
from app.models import *


def check_if_locked_by_user(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    locked = s.query(Panels).filter(or_(and_(Panels.id == panel_id, Panels.locked == user_id),
                                        and_(Panels.locked == None, Panels.id == panel_id))).count()
    if locked == 0:
        return False
    else:
        return True


def check_virtualpanel_status_query(s, id):
    """
    query to check the status of a virtual panel - returns fields required to decide status of a panel

    :param s: db session
    :param id: panel id
    :return: result of query
    """

    panels = s.query(VirtualPanels, VPRelationships).filter_by(id=id).join(VPRelationships). \
        values(VirtualPanels.name, \
               VirtualPanels.current_version, \
               VPRelationships.last, \
               VPRelationships.intro)

    return panels

@message
def lock_panel(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    lock = s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: user_id})
    s.commit()
    return True
from app.panel_pal import message
from app.models import *


@message
def toggle_admin_query(s,user_id):
    """
    toggles a user admin rights
    :param s: database session
    :param user_id: the id of the user
    :return: True or False
    """
    query = s.query(Users).filter(Users.id == user_id).values(Users.admin)
    for i in query:
        if i.admin == 1:
            new_value = 0
        else:
            new_value = 1
    try:
        s.query(Users).filter_by(id=user_id).update({Users.admin: new_value})
        s.commit()
        return True
    except:
        return False


@message
def create_user(s,username):
    """
    create a user
    :param s: database session
    :param username: the username of the new user
    :return: True or False
    """
    user = Users(username=username,admin=0)
    try:
        s.add(user)
        s.commit()
        return True
    except:
        return False

def get_user_id_by_username(s, username):
    user = s.query(Users).filter_by(username=username).values(Users.username, Users.id)
    for i in user:
        return i.id


def check_if_admin(s,username):
    """
    check if the user is an admin

    :param s: database session
    :param username: the username of the user
    :return: True or False for admin status
    """
    user_id = get_user_id_by_username(s,username)
    query = s.query(Users).filter(Users.id == user_id).values(Users.admin)
    for i in query:
        if i.admin == 1:
            return True
        else:
            return False

#TODO ?mod_admin queries
def get_users(s):
    """
    gets all users
    :param s: database session
    :return: sql alchemy generator object
    """
    users = s.query(Users).order_by(Users.username).values(Users.id,Users.username,Users.admin)
    return users



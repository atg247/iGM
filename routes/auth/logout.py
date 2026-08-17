from flask import flash, redirect, session, url_for
from flask_login import login_required, logout_user

from . import auth_bp


@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    flash('You have successfully logged out.', 'info')

    return redirect(url_for('routes.index'))

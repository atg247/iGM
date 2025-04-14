from flask import redirect, url_for, flash, session
from flask_login import logout_user, login_required

from . import auth_bp

@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    flash('You have successfully logged out.', 'info')

    return redirect(url_for('routes.index'))


from flask import Blueprint, render_template
from flask_login import login_required

battle_bp = Blueprint('battle', __name__)

@battle_bp.route('/battle')
@login_required
def index():
    return render_template('battle.html')

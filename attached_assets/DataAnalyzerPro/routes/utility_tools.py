from flask import Blueprint, render_template

utility_tools = Blueprint('utility_tools', __name__)

@utility_tools.route('/mb-gb-converter')
def mb_gb_converter():
    return render_template('mb_gb_converter.html')

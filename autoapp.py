from powonline.web import make_app
from powonline.util import colorize_werkzeug
from gouge.colourcli import Simple
Simple.basicConfig(level=0)
colorize_werkzeug()
APP = make_app('postgresql://exhuma@/powonline')
APP.run(debug=True, host='0.0.0.0')

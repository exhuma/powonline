from powonline.web import make_app
APP = make_app()
APP.run(debug=True, host='0.0.0.0')

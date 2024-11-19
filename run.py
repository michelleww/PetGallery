#!../venv/bin/python
from app import webapp
webapp.run('0.0.0.0', 5000, debug=True)

# For AWS Instance 
#!venv/bin/python
#from app import webapp
#webapp.run()
#webapp.run(host='0.0.0.0')
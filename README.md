# vpnconservice
Simple nginx+gunicorn+flask app for wireguard peers service

Before the first launch, you must create an appconf.txt in work dir with:
/    The password specified in the request header "Auth" : (any line)
/    The working directory in which the project is located. Example: /ur/work/dir/ (Required / at the end)
/    The address of the server where the project is running and the port that wireguard listens to. Example: 0.0.0.0:0000
/    The answer to the question: "Running in test mode?(YES/NO)"
    
If you run app properly, you can go to /api/1.0/doc to find the API documentation

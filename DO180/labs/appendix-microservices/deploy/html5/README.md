# DO180 To Do HTML5 front-end as a container

Do not start this one directly: The scripts for each version of the API container will start the front-end container with correct configs.

This front end app has the API location hard-coded (hostname and port). A real-world app would work this way using a well-known DNS FQDN.

Any browser you use to test the application needs api.lab.example.com resolving to the back end IP or some IP that port-forwards to it.

The application runs on the Apache root, so it is accessed as http://127.0.0.1:30000/


var os = require('os');

exports.context = function(server, path) {
    if (!server)
        done('has to provide a restify server object');
        
    server.get(path + '/host', this.serverInfo);
};

exports.serverInfo = function(req, res, next) {
    var address;
    var ifaces = os.networkInterfaces();

    for (var dev in ifaces) {
        var iface = ifaces[dev].filter(function(details) {
            return details.family === 'IPv4' && details.internal === false;
        });
        if (iface.length > 0)
            address = iface[0].address;
    }

    var reply = {
        ip: address,
        hostname: os.hostname()
    };
    res.json(reply);
    next();
};


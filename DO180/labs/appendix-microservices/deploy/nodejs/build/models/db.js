
module.exports.params = {
    dbname: process.env.MYSQL_DATABASE,
    username: process.env.MYSQL_USER,
    password: process.env.MYSQL_PASSWORD,
    params: {
        host: process.env.MYSQL_SERVICE_HOST,
        port: process.env.MYSQL_SERVICE_PORT,
        dialect: 'mysql'
    }
};


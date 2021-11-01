
module.exports.params = {
  dbname: process.env.MYSQL_DATABASE,
  username: process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  params: {
      host: '10.88.100.101',
      port: '3306',
      dialect: 'mysql'
  }
};

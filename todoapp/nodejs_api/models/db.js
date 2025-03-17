const { Sequelize, DataTypes } = require('sequelize');

const sequelize = new Sequelize(
  process.env.DB_NAME || 'todoapp',
  process.env.DB_USER || 'root',
  process.env.DB_PASSWORD || 'password',
  {
    host: process.env.DB_HOST || 'localhost',
    port: process.env.DB_PORT || 3306,
    dialect: 'mysql'
  }
);

const Item = sequelize.define('Item', {
  description: {
    type: DataTypes.STRING,
    allowNull: false
  },
  done: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  }
});

module.exports = { sequelize, Item };

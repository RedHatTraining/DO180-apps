const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const Item = sequelize.define('Item', {
    id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true
    },
    description: {
        type: DataTypes.STRING,
        allowNull: false
    },
    done: {
        type: DataTypes.BOOLEAN,
        defaultValue: false
    }
}, {
    timestamps: false
});

module.exports = Item;
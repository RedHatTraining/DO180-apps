var Sequelize = require("sequelize");

var Item = undefined;

module.exports.connect = function(params, callback) {
    var sequlz = new Sequelize(
        params.dbname, params.username, params.password,
        params.params);
    Item = sequlz.define('Item', {
        id: { type: Sequelize.BIGINT,
            primaryKey: true, unique: true, allowNull: false,
            autoIncrement: true },
        description: { type: Sequelize.STRING,
            allowNull: true },
        done: { type: Sequelize.BOOLEAN,
            allowNull: true }
    }, {
        timestamps: false,
        freezeTableName: true
    });
    // drop and create tables, better done globally
    /*
    Item.sync({ force: true }).then(function() {
        callback();
    }).error(function(err) {
        callback(err);
    });
    */
}

exports.disconnect = function(callback) {
    //XXX shouln'd to something to close or release the db connection?
    callback();
}

exports.create = function(description, done, callback) {
    Item.create({
        //id: id,
        description: description,
        done: (done) ? true : false
    }).then(function(item) {
        callback(null, item);
    }).error(function(err) {
        callback(err);
    });
}

exports.update = function(key, description, done, callback) {
    Item.findOne({ where:{ id: key } }).then(function(item) {
        if (!item) {
            callback(new Error("Nothing found for key " + key));
        }
        else {
            item.update({
                description: description,
                done: (done) ? true : false
            }).then(function() {
                callback(null, item);
            }).error(function(err) {
                callback(err);
            });
        }
    }).error(function(err) {
        callback(err);
    });
}


exports.read = function(key, callback) {
    Item.findOne({ where:{ id: key } }).then(function(item) {
        if (!item) {
            callback(new Error("Nothing found for key " + key));
        }
        else {
            //XXX why recreating the item object?
            callback(null, {
                id: item.id,
                description: item.description,
                done: item.done
            });
        }
    }).error(function(err) {
        callback(err);
    });
}

exports.destroy = function(key, callback) {
    Item.findOne({ where:{ id: key } }).then(function(item) {
        if (!item) {
            callback(new Error("Nothing found for " + key));
        }
        else {
            item.destroy().then(function() {
                callback(null, item);
            }).error(function(err) {
                callback(err);
            });
        }
    }).error(function(err) {
        callback(err);
    });
}

exports.countAll = function(callback) {
    Item.findAll({ attributes: [[Sequelize.fn('COUNT', Sequelize.col('id')), 'no_items']] } ).then(function(n) {
        callback(null, n[0].get('no_items'));
    }).error(function(err) {
        callback(err);
    });
   //callback(null, 100);
}

exports.listAll = function(page, sortField, sortDirection, callback) {
    Item.findAll({ offset: 10 * (page - 1), limit: 10,  order: [[sortField, sortDirection]] }).then(function(items) {
        var theitems = [];
        items.forEach(function(item) {
            //XXX why recreating the item objects for theitems?
            theitems.push({
                id: item.id, description: item.description, done: item.done });
        });
        callback(null, theitems);
    }).error(function(err) {
        callback(err);
    });
}


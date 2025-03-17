const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const db = require('./models/db');
const itemsController = require('./controllers/items');
const serverInfoController = require('./controllers/serverinfo');

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

itemsController(app);
serverInfoController(app);

const port = process.env.PORT || 8080;
db.sequelize.sync().then(() => {
  app.listen(port, () => {
    console.log(`TodoApp listening on port ${port}`);
  });
}).catch(err => {
  console.error('Database sync failed:', err);
});

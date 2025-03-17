const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const db = require('./models/db');
const itemsController = require('./controllers/items');
const serverInfoController = require('./controllers/serverinfo');

// Middleware para parsear JSON y datos de formularios
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Controladores
itemsController(app);
serverInfoController(app);

// Ruta principal para verificar que el servidor responde
app.get('/', (req, res) => {
  res.send('✅ TodoApp está corriendo correctamente.');
});

// Puerto de escucha
const port = process.env.PORT || 8080;

// Sincronización con la base de datos y arranque del servidor
db.sequelize.sync().then(() => {
  app.listen(port, () => {
    console.log(`✅ TodoApp escuchando en el puerto ${port}`);
  });
}).catch(err => {
  console.error('❌ Fallo al sincronizar con la base de datos:', err);
});

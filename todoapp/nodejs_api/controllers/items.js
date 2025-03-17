module.exports = function(app) {
  const db = require('../models/db');
  const Item = db.Item;

  app.get('/items', async (req, res) => {
    const items = await Item.findAll();
    res.json(items);
  });

  app.post('/items', async (req, res) => {
    const newItem = await Item.create(req.body);
    res.json(newItem);
  });

  app.delete('/items/:id', async (req, res) => {
    await Item.destroy({ where: { id: req.params.id }});
    res.json({ message: 'Item deleted' });
  });
};

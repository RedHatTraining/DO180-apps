module.exports = function(app) {
  app.get('/info', (req, res) => {
    res.json({
      uptime: process.uptime(),
      message: 'OK',
      timestamp: Date.now()
    });
  });
};

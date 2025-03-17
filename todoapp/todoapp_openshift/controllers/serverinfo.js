module.exports = function(app) {
  app.get('/api/serverinfo', (req, res) => {
    res.json({
      uptime: process.uptime(),
      message: 'OK',
      timestamp: Date.now()
    });
  });
};

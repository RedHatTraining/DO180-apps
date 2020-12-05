const express = require('express');
const router = express.Router();
const fetch = require("node-fetch");
require('dotenv').config();
const OWM_API_KEY = process.env.OWM_API_KEY || 'invalid_key';
const UNITS = process.env.UNITS || 'metric';

/* GET home page. */
router.get('/', function(req, res) {
  res.render('index', { weather: null, err: null });
});

router.post('/get_weather', async function (req,res) {
  let city = req.body.city;
  let url = `http://api.openweathermap.org/data/2.5/weather?q=${city}&units=${UNITS}&appid=${OWM_API_KEY}`;

  try {
    let data = await fetch(url);
    let weather = await data.json();
    console.log(weather);
    if(weather.cod == '404' && weather.main == undefined) {
      res.render('index', {weather: null, error: 'Error: Unknown city'});
    }
    else if (weather.cod == '401' && weather.main == undefined) {
      res.render('index', {weather: null, error: 'Error: Invalid API Key. Please see http://openweathermap.org/faq#error401 for more info.'});
    }
    else {
      let unit_hex = (UNITS == 'imperial') ? '&#8457' : '&#8451';
      res.render('index', {weather: weather, error: null, units: unit_hex});
    }
  }
  catch (err) {
    console.log(err);
    res.render('index', {weather: null, error: 'Error: Unable to invoke OpenWeatherMap API'});
  }

});

module.exports = router;

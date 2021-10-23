<html>
<head>
      <title>Converting Temperatures</title>
      <meta charset="utf-8">
</head>
<body>
      <form name="form1" method="POST" action="<?php echo $_SERVER["PHP_SELF"]; ?>">

<table>
<tr>
    <td>Enter the temperature to convert:</td>
    <td><input type="text" name="temp" id="temp" size="10"></td>
</tr>

<tr>
    <td>Convert to:</td>
    <td><select name="scale" id="scale" size="1">
               <option disabled>Select the scale</option>
               <option value="c">Celsius</option>
               <option value="f">Fahrenheit</option>
        </select>
    </td>
</tr>

<tr>
    <td><input type="submit" name="btnConvert" id="btnConvert" value="Convert"></td>
    <td><input type="reset" name="btnReset" id="btnReset" value="Reset"></td>
</tr>



</form>

<?php
 function convert($value, $type){
    if($type== "f"){
       return (((9/5)*$value) +(32));
   }
    elseif ($type== "c"){
       return (($value - 32) * (5/9));
   }
}

if (isset($_POST['btnConvert'])) {
$temp = $_POST['temp'];
$scale = $_POST['scale'];
$converted = convert($temp, $scale);
echo "The original temperature, $temp, converted is $converted.";
}
?>

    </body>
</html>

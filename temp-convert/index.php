<?php

/*
header("Content-Type: text/plain");

if  (!isset($_GET['c'])) {
	echo "Usage: ?c=25 converts 25°C to Fahrenheit\n";
	exit;
}

$c = floatval($_GET['c']);
$f = ($c * 9/5) + 32;

echo "{$c}C = {$f}F\n";
*/

?>


<form method="get">
    <label>Enter Celsius:</label>
    <input type="number" name="c" step="any">
    <button type="submit">Convert</button>
</form>

<hr>

<?php
if (isset($_GET['c'])) {
    $c = floatval($_GET['c']);
    $f = $c * 9/5 + 32;
    echo "<p>{$c}°C = {$f}°F</p>";
}
?>


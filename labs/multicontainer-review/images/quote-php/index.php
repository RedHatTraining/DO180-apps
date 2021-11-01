<?php
    $link = mysqli_connect($_ENV["MYSQL_SERVICE_HOST"],"user1","mypa55","quotes", $_ENV["MYSQL_SERVICE_PORT"]) or die("Error " . mysqli_error($link)); 

    $query = "SELECT count(*) FROM quote";
    $result = $link->query($query) or die("Error in the consult.." . mysqli_error($link));
    $row = mysqli_fetch_array($result);
    mysqli_free_result($result);

    $id = rand(1,$row[0]);

    $query = "SELECT msg FROM quote WHERE id = " . $id;
    $result = $link->query($query) or die("Error in the consult.." . mysqli_error($link));
    $row = mysqli_fetch_array($result);
    mysqli_free_result($result);

    print $row[0] . "\n";

    mysqli_close($link);
?>

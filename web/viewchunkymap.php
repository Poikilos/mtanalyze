<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html style="width:100%; height:100%">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>Chunkymap</title>
<?php
$html4_mode_enable=false; //if true, does not echo canvas nor client-side scripting
if ($html4_mode_enable===true) {
echo '<meta http-equiv="refresh" content="45">';
}
echo ' <!-- -->
</head>
<body style="font-family:calibri,Droid Sans,Apple SD Gothic Neo,sans; font-size: 120%;  width:100%; height:100%; margin:0; padding:0" topmargin="0" leftmargin="0" rightmargin="0" bottommargin="0">
';

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
//echo "php started...";

///// SHOW EXPIRED PLAYERS: ///////////
$show_expired_players_enable = false; //
///////////////////////////////////////
//make sure you set this here, otherwise players can override it

if (is_file('chunkymap.php')) {
    //echo "including...";
    include_once('chunkymap.php');
    //echo "about to call echo_chunkymap_as_chunk_table...";

    //The following is not needed, since chunkymap.php should be included above and puts all $_REQUEST array variables into $GLOBALS array
    //if (!isset($_REQUEST['x'])) {//if (!isset($x)) {
    //  $x=0;
    //}
    //else $x=$_REQUEST['x'];
    //echo "<center>";
    //echo "<h1>";
    //echo_map_heading_text();
    //echo "</h1>";
    //echo "</center>";
    set_chunkymap_view($x,$z,$zoom);
    //echo "<table><tr><td style=\"text-align:left\">";
    $show_player_names_enable=true;
    $decachunks_enable=false; //(this should normally be false) if true, uses 16x16 png files instead of the 160x160 decachunks; it is slower but may have more of the map during times when new chunks are explored but before the render queue is done and the decachunk images are created from the chunk images.);
    $chunks_enable=false; //(this should normally be false) if true, uses 16x16 png files instead of the 160x160 decachunks; it is slower but may have more of the map during times when new chunks are explored but before the render queue is done and the decachunk images are created from the chunk images.);
    $visual_debug_enable=false; //if true, this renders colors based on yml files instead of drawing images (and does not echo images at all)
    $html4_mode_enable=false;
    $append_vars = "";
    if (isset($x)) {
        $append_vars.="&x=$x";
    }
    if (isset($z)) {
        $append_vars.="&z=$z";
    }
    if (isset($zoom)) {
        $append_vars.="&zoom=$zoom";
    }
    // if (!isset($world_name)) {
        // if ($handle = opendir($chunkymapdata_worlds_path)) {
            // while (false !== ($file_name = readdir($handle))) {
                // if (substr($file_name, 0, 1) != ".") {
                    // $file_path = $chunkymapdata_worlds_path."/".$file_name;
                    // if (is_dir($file_path)) {
                        // echo "<a href=\"?world_name=$file_name$append_vars\">$file_name</a>";
                        // //$world_name=$file_name;
                        // //break;
                    // }
                // }
            // }
            // closedir($handle);
        // }
    // }
    echo "Press F5 key on your keyboard to refresh player locations.<br/>";
    echo_chunkymap_canvas($show_player_names_enable,$decachunks_enable,$chunks_enable,$visual_debug_enable,$html4_mode_enable);
    //echo_chunkymap_as_chunk_table(false);
    //echo_decachunk_table();
    //echo "</td></tr></table>";
    //echo "returned from echo_chunkymap_as_chunk_table.";
}
else {
    echo "missing chunkymap.php";
}
?>
</body>
</html>


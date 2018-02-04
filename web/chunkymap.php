<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
if (($_SERVER['PHP_SELF'] == "chunkymap.php") or endsWith($_SERVER['PHP_SELF'],"/chunkymap.php")) {
	echo "<html><body style=\"font-family:calibri,arial,helvetica,sans\">This is the backend--don't call it directly. instead do include_once('chunkymap.php'); To use the map, go to <a href=\"viewchunkymap.php\">viewchunkymap.php</a> instead.</body></html>";
}
//date.timezone = "UTC";
ini_set("date.timezone", "UTC"); //seems to have to effect on wrong time returned by time() (returns UTC-5 though server is in UTC-4 and BIOS is UTC)
date_default_timezone_set("UTC"); //seems to have to effect on wrong time returned by time() (returns UTC-5 though server is in UTC-4 and BIOS is UTC)
//otherwise try AntonioCS's Feb 24 '15 at 17:06 edit of Gordon's Apr 9 '10 at 12:59  answer from <http://stackoverflow.com/questions/2607545/display-time-date-in-specific-timezone-using-date-function>:
//$datetime = new DateTime; // current time = server time
//$otherTZ  = new DateTimeZone('UTC');
//$datetime->setTimezone($otherTZ); // calculates with new TZ now
$to_utc_debug_value = 5*60*60; //only way to get to UTC for unknown reason
$auto_choose_enable = false;
$auto_choose_enable = false;
$minute=60;
$player_file_age_expired_max_seconds=20*$minute-1;
$player_file_age_idle_max_seconds=5*$minute-1;
$show_missing_data_msg_enable = true;

//NOTE: for parse errors, MUST add the following line to  php.ini (such as /etc/php5/apache2/php.ini): display_errors = on
if (is_file('browser.php')) {
    include_once('browser.php');
}
else {
    echo "<!--missing browser.php...-->";
}
$chunkymap_anchor_name="chunkymap_top";
$is_verbose = false;
if ($is_verbose) echo "REQUEST...";
foreach($_REQUEST as $key => $value) {
    //in case auto_globals is not enabled
    $GLOBALS[$key]=$value;
    if ($is_verbose) echo "$key:$value...";
}
if ($is_verbose) echo "timezone...";
date_default_timezone_set('EST'); //required by PHP >=5.1.0

if ($is_verbose) echo "globals...";
//$x=0;
//$z=0;
//$zoom=25;
if (!isset($x)) {
    $x=0;
}
if (!isset($z)) {
    $z=0;
}
if (!isset($zoom)) {
    $zoom=.25;
}

$chunkymapdata_path = "chunkymapdata";
$chunkymapdata_worlds_path = $chunkymapdata_path."/worlds";
$chunkymapdata_thisworld_path = null;
$showplayers=true;

// NOT OPTIONAL for table version:
$chunkymap_tile_original_w=16;
$chunkymap_tile_original_h=16;

$chunk_dimension_min=$chunkymap_tile_original_w;
if ($chunkymap_tile_original_h<$chunk_dimension_min) $chunk_dimension_min=$chunkymap_tile_original_h;
$chunkymap_change_zoom_multiplier=1.5;
$chunkymap_camera_pan_delta=.5;
$chunkymap_view_min_zoom=0.0173415299; //1.0/$chunk_dimension_min; //should be a number that would get to exactly 100 eventually if multiplied by chunkymap_zoom_delta repeatedly (such as 0.09765625 if chunkymap_zoom_delta were 2); 0.005 was avoided since tiles used to be 80x80 pixels
$chunkymap_view_max_zoom=16585998.48141; //13107200.0;

$decachunk_prefix_string="decachunk_";
$decachunk_prefix_then_x_string=$decachunk_prefix_string."x";
$chunk_prefix_string="chunk_";
$chunk_prefix_then_x_string=$chunk_prefix_string."x";
$z_opener="z";
$dot_yaml=".yml";
$decachunk_dot_and_ext=".jpg";
$chunk_dot_and_ext = ".png";

//$more_attribs_string="; -webkit-filter: opacity(0%); filter: opacity(0%)";
$more_attribs_string="";
$td_decachunk_placeholder_content="<!--widening table--><img src=\"chunkymapdata/images/decachunk_blank.jpg\" style=\"width:100%; background-color:black".$more_attribs_string."\"/>";
$td_chunk_placeholder_content="<!--widening table--><img src=\"chunkymapdata/images/chunk_blank.jpg\" style=\"width:100%; background-color:black".$more_attribs_string."\"/>";
$td_1px_placeholder_content="<!--widening table--><img src=\"chunkymapdata/images/chunk_blank.jpg\" style=\"width:1px; background-color:black".$more_attribs_string."\"/>";


function echo_error($val) {
    if (!isset($val)) {
        $val="Unknown Error";
    }
    echo '<span style="color:red">'.$val.'</span><br/>'."\n";
}

function get_dict_from_conf($path, $assignment_operator) {
    global $is_verbose;
    if ($is_verbose) echo "get_dict...";
    $handle = fopen($path, "r");
    $result = null;
    if ($handle) {
        while (($line = fgets($handle)) !== false) {
            $line_strip = trim($line);
            if (strlen($line_strip)>0) {
                if (substr($line_strip,0,1)!="#") {
                    $ao_index = strpos($line_strip, $assignment_operator);
                    if ($ao_index>0 and $ao_index<(strlen($line_strip)-1)) { //skip blank variable OR value
                        $found_name = substr($line_strip, 0, $ao_index);
                        $found_value_index = $ao_index + 1;
                        $found_value = substr($line_strip, $found_value_index, strlen($line_strip)-$found_value_index);
                        if ($result===null) {
                            $result = array();
                        }
                        $result[$found_name]=$found_value;
                    }
                }
            }
        }
        fclose($handle);
    } else {
        echo "<span style=\"color:read\">Failed to read $path</span> (run chunkymap-cronjob script as root first, otherwise see README.md in minetest-chunkymap to ensure installation is correct).<br/>";
    }
    return $result;
}//end get_dict_from_conf



$map_dict = null;

//startsWith and endsWith are from:
//Salmon A. stackoverflow. <http://stackoverflow.com/questions/834303/startswith-and-endswith-functions-in-php>. 5 Feb 2016. 19 Feb, 2016.
function startsWith($haystack, $needle) {
    // search backwards starting from haystack length characters from the end
    return $needle === "" || strrpos($haystack, $needle, -strlen($haystack)) !== false;
}
function endsWith($haystack, $needle) {
    // search forward starting from end minus needle length characters
    return $needle === "" || (($temp = strlen($haystack) - strlen($needle)) >= 0 && strpos($haystack, $needle, $temp) !== false);
}

//NOTE: This function is here since the builtin is_int checks type (which is not needed in this webapp) and the builtin is_numeric includes decimal and exponent (see http://php.net/manual/en/function.is-numeric.php)
function is_int_string($val) {
    global $is_verbose;
    if ($is_verbose) echo "is_int_string...";
    $result = true;
    $int_chars="0123456789-";
    for ($i=0; $i<strlen($val); $i++) {
        $digit_index = strpos($int_chars, substr($val, $i, 1));
        if ($digit_index===false) {
            $result = false;
            break;
        }
    }
    return $result;
}
function set_chunkymap_view($set_chunkymap_view_x, $set_chunkymap_view_z, $set_chunkymap_view_zoom) {
    global $x;
    global $z;
    global $zoom;
    $x = $set_chunkymap_view_x;
    $z = $set_chunkymap_view_z;
    $zoom = $set_chunkymap_view_zoom;
}

function echo_map_heading_text() {
    echo "Chunkymap";
    //echo "Map of ";
    //echo_worldname();
}
// function echo_worldname() {
    // global $map_dict;
    // if (isset($map_dict["world_name"])) {
        // echo $map_dict["world_name"];
    // }
    // else echo "<span style=\"color:red\">(missing world name)</span>";
// }
function get_chunk_folder_path_from_chunky_coords($chunky_x, $chunky_z) {
	global $chunkymapdata_thisworld_path;
	//NOTE: floor converts -.5 to -1 (and -1.5 to -2) but .5 to 0
	$decachunk_x = get_decachunky_coord_from_chunky_coord($chunky_x);
	$decachunk_z = get_decachunky_coord_from_chunky_coord($chunky_z);
	//if ($chunky_x<0) { $decachunk_x = $chunky_x + $chunky_x%10; }
	//else { $decachunk_x = $chunky_x - $chunky_x%10; }
	//if ($chunky_z<0) { $decachunk_z = $chunky_z + $chunky_z%10; }
	//else { $decachunk_z = $chunky_z - $chunky_z%10; }
	$result = $chunkymapdata_thisworld_path.'/16px/'.$decachunk_x.'/'.$decachunk_z;
	return $result;
}

function get_decachunk_folder_path_from_location($location_x, $location_z) {
	global $chunkymapdata_thisworld_path;
	//NOTE: floor converts -.5 to -1 (and -1.5 to -2) but .5 to 0
	$chunky_x = get_chunky_coord_from_location($location_x);
	$chunky_z = get_chunky_coord_from_location($location_z);
	$decachunky_x = get_decachunky_coord_from_chunky_coord($chunky_x);
	$decachunky_z = get_decachunky_coord_from_chunky_coord($chunky_z);
	$hectochunk_x = get_hectochunky_coord_from_decachunky_coord($decachunky_x);
	$hectochunk_z = get_hectochunky_coord_from_decachunky_coord($decachunky_z);
	$result = $chunkymapdata_thisworld_path.'/160px/'.$hectochunk_x.'/'.$hectochunk_z;
	return $result;
}

function get_decachunk_folder_path_from_decachunk($chunky_x, $chunky_z) {
	global $chunkymapdata_thisworld_path;
	//NOTE: floor converts -.5 to -1 (and -1.5 to -2) but .5 to 0
	$hectochunk_x = get_hectochunky_coord_from_decachunky_coord($chunky_x);
	$hectochunk_z = get_hectochunky_coord_from_decachunky_coord($chunky_z);
	$result = $chunkymapdata_thisworld_path.'/160px/'.$hectochunk_x.'/'.$hectochunk_z;
	return $result;
}

function get_chunky_coord_from_location($location_coord) {
	$chunk_coord = intval(floor((float)$location_coord/16));
	return $chunk_coord;
}

function get_decachunky_coord_from_chunky_coord($chunky_x) {
	return intval(floor((float)$chunky_x/10.0));
}

function get_hectochunky_coord_from_decachunky_coord($chunky_x) {
	return intval(floor((float)$chunky_x/10.0));
}

function get_decachunky_coord_from_location($location_x) {
	$chunk_x = get_chunky_coord_from_location($location_x);
	$decachunk_x = get_decachunky_coord_from_chunky_coord($chunk_x);
	return $decachunk_x;
}

function get_decachunk_image_path_from_decachunk($decachunky_x, $decachunky_z) {
	return get_decachunk_folder_path_from_decachunk($decachunky_x, $decachunky_z)."/".get_decachunk_image_name_from_decachunk($decachunky_x, $decachunky_z);
}

function get_decachunk_image_name_from_decachunk($decachunky_x, $decachunky_z) {
	global $decachunk_prefix_string;
	global $decachunk_dot_and_ext;
	return "$decachunk_prefix_string"."$decachunky_x"."z"."$decachunky_z"."$decachunk_dot_and_ext";
}
function get_chunk_yaml_path_from_chunky_coords($chunky_x, $chunky_z) {
	return get_chunk_folder_path_from_chunky_coords($chunky_x, $chunky_z).'/'.get_chunk_yaml_file_name($chunky_x, $chunky_z);
}
function get_chunk_image_path_from_chunky_coords($chunky_x, $chunky_z) {
	return get_chunk_folder_path_from_chunky_coords($chunky_x, $chunky_z).'/'.get_chunk_file_name($chunky_x, $chunky_z);
}
function get_chunk_yaml_file_name($chunky_x, $chunky_z) {
	global $chunk_prefix_then_x_string;
	global $dot_yaml;
	global $z_opener;
	return $chunk_prefix_then_x_string.$chunky_x.$z_opener.$chunky_z.$dot_yaml;
}
function get_chunk_file_name($chunky_x, $chunky_z) {
	global $chunk_prefix_then_x_string;
	global $dot_yaml;
	global $z_opener;
	global $chunk_dot_and_ext;
	return $chunk_prefix_then_x_string.$chunky_x.$z_opener.$chunky_z."$chunk_dot_and_ext";
}

function get_javascript_bool_value($this_bool) {
	$result = "false";
	if ($this_bool == true) {
		$result = "true";
	}
	return $result;
}

function get_javascript_int_value($this_val) {
	$result = $this_val;
	if ($this_val === null) {
		$result = "null";
	}
	else {
		$this_val = intval($this_val);
		$result = "$this_val";
	}
	return $result;
}

$show_utc_msg_enable = true;

function get_markers_from_dir($chunkymap_markers_path) {
	global $chunkymapdata_thisworld_path;
	global $player_file_age_expired_max_seconds;
	global $player_file_age_idle_max_seconds;
	global $show_expired_players_enable;
	global $to_utc_debug_value;
	global $show_utc_msg_enable;
	$datetime = new DateTime; // current time = server time
	$otherTZ  = new DateTimeZone('UTC');
	$datetime->setTimezone($otherTZ); // calculates with new TZ now
	//date_add($datetime, date_interval_create_from_date_string('5 hours')); //does nothing for unknown reason
	$now_timestamp = time($datetime);
	$now_timestamp += $to_utc_debug_value; //can't get UTC any other way for unknown reason
	if ($show_utc_msg_enable) {
		echo "using ".DATE("Y-m-d H:i e",$now_timestamp)." as UTC<br/>"."\n";
		$show_utc_msg_enable = false;
	}
	if ($show_expired_players_enable===true) {
		echo "show_expired_players_enable:true";
	}
	$markers=array();
	$markers_count=0;
	//echo phpversion()."<br/>"."\n";
	if (is_dir($chunkymap_markers_path)) {
		if ($handle = opendir($chunkymap_markers_path)) {
			while (false !== ($file_name = readdir($handle))) {
				if (substr($file_name, 0, 1) != ".") {
					$file_name_lower = strtolower($file_name);
					if (endsWith($file_name_lower, ".yml")) {
						$file_path = $chunkymap_markers_path."/".$file_name;
						$marker_vars = get_dict_from_conf($file_path, ":");
						if (isset($marker_vars["x"]) and isset($marker_vars["z"])) {
							$is_expired=false;
							$is_idle=false;
							if (isset($marker_vars["utc_mtime"])) {
								$last_player_update_time = strtotime($marker_vars["utc_mtime"]);
								
								if ($now_timestamp-$last_player_update_time > $player_file_age_expired_max_seconds) {
									$is_expired=true;
									//echo "expired<br/>"."\n";
								}
								elseif ($now_timestamp-$last_player_update_time > $player_file_age_idle_max_seconds) {
									$is_idle=true;
									//echo "idle<br/>"."\n";
								}
								else {
									//echo "not expired since ".$marker_vars["name"]."'s utc_mtime is ".DATE("Y-m-d H:i",$last_player_update_time)." <br/>"."\n";
									//echo " current date is ".DATE("Y-m-d H:i",$now_timestamp)." <br/>"."\n";
								}
								if ($is_expired===false) {
									$markers[$markers_count]["utc_mtime"] = $marker_vars["utc_mtime"];
								}
							}
							if (($show_expired_players_enable===true) or ($is_expired===false)) {
								$markers[$markers_count]["x"] = $marker_vars["x"];
								$markers[$markers_count]["z"] = $marker_vars["z"];
								$markers[$markers_count]["is_idle"] = $is_idle;
								$markers[$markers_count]["is_expired"] = $is_expired;
								if (isset($marker_vars["y"])) {
									$markers[$markers_count]["y"] = $marker_vars["y"];
								}
								if (isset($marker_vars["image"])) {
									$try_path = "$chunkymapdata_thisworld_path/".$marker_vars["image"];
									if (is_file($try_path)) {
										$markers[$markers_count]["image"] = $try_path; //this is the normal place to store them actually
									}
									else {
										$markers[$markers_count]["image"] = $marker_vars["image"];
									}
								}
								else {
									if (isset($marker_vars["index"])) {
										$try_path = "$chunkymapdata_thisworld_path/players/".$marker_vars["index"].".jpg";
										if (is_file($try_path)) {
											$markers[$markers_count]["image"] = $try_path;
											echo_error("detected image $try_path\r\n");
										}
										else {
											
											$try_path = "$chunkymapdata_thisworld_path/players/".$marker_vars["index"].".png";
											if (is_file($try_path)) {
												$markers[$markers_count]["image"] = $try_path;
											}
										}
									}
									else {
										echo_error("missing index in marker file $file_name\r\n");
									}
								}
								if (isset($marker_vars["name"])) {
									$markers[$markers_count]["name"] = $marker_vars["name"];
								}
								if (isset($marker_vars["index"])) {
									$markers[$markers_count]["index"] = $marker_vars["index"]; //for ajax to get player location with neither playerid nor name known
								}
								if (isset($marker_vars["playerid"])) {
									$markers[$markers_count]["playerid"] = $marker_vars["playerid"];
								}
								$markers_count+=1;
							}
							
						}
						else {
							echo_error("Bad location in marker file '$file_path'");
						}
					}
				}
			}
		}
	}
	else {
		echo "<!--missing $chunkymap_markers_path-->";
	}
	return $markers;
}


//chunks_enable: shows chunk png images instead of decachunk jpg images (slower)
//visual_debug_enable: draws colored rectangles based on yml files instead of drawing images
function echo_chunkymap_canvas($show_player_names_enable, $decachunks_enable, $chunks_enable, $visual_debug_enable, $html4_mode_enable) {
    global $x;
    global $z;
    global $zoom;
    global $chunkymap_view_max_zoom;
    global $chunkymap_view_min_zoom;
	global $showplayers;
	global $chunkymap_change_zoom_multiplier;
	global $chunkymap_camera_pan_delta;
	global $world_name;
	global $chunkymapdata_thisworld_path;
	$is_ready = check_world();
	
	if ($html4_mode_enable!==true) {
		echo '<noscript>
 For full functionality of this site it is necessary to enable JavaScript.
 Here are the <a href="http://www.enable-javascript.com/" target="_blank">
 instructions how to enable JavaScript in your web browser</a>.
</noscript>';
	}
	if ($is_ready) {
		if (isset($world_name)) {
			$chunks_per_tile_x_count = 10;
			$chunks_per_tile_z_count = 10;
			
			//use decachunk jpgs by default for speed:
			$tile_w = 160;
			$tile_h = 160;
			
			if (isset($chunks_enable) and ($chunks_enable===true)) {
				$tile_w = 16;
				$tile_h = 16;
				$chunks_per_tile_x_count = 1;
				$chunks_per_tile_z_count = 1;
			}
			else {
				$chunks_enable=false;
			}
			
			$locations_per_tile_x_count = $chunks_per_tile_x_count*16;
			$locations_per_tile_z_count = $chunks_per_tile_z_count*16;
				
			if ($zoom<$chunkymap_view_min_zoom) $zoom = $chunkymap_view_min_zoom;
			if ($zoom>$chunkymap_view_max_zoom) $zoom = $chunkymap_view_max_zoom;

			$EM_PER_WIDTH_COUNT = 800.0/12.0; //ultimately derived from 12pt font on 800x600 display--no really, this is right
			
			$camera_w = (800) * (1.0/$zoom); //screen should be 800pt wide always (so 12pt is similar on all screens and only varies with physical size of screen in inches, and since pt was invented to replace px)
			$camera_left = $x-$camera_w/2.0;
			
			$camera_h = $camera_w; //start with square camera to make sure enough chunks are loaded and since neither screen height nor ratio can be known from php since it is only run on server-side
			$camera_top = $z+$camera_h/2.0; //plus since cartesian until drawn [then flipped]
			
			$chunky_view_x = get_chunky_coord_from_location($x);
			$chunky_view_z = get_chunky_coord_from_location($z);

			#tile is either chunk or decachunk
			$min_tiley_x = -1;
			$max_tiley_x = 0;
			$min_tiley_z = -1;
			$max_tiley_z = 0;
			
			$camera_right = $camera_left+$camera_w;
			$camera_bottom = $camera_top-$camera_h; //minus since cartesian until drawn [then flipped]
			
			//Only whether the near edges are in the canvas matters (get bottom of max since always cartesian until drawn [then inverted]):
			$min_tiley_x__chunk_location_right = $min_tiley_x*$locations_per_tile_x_count+$locations_per_tile_x_count;
			$max_tiley_x__chunk_location_left = $max_tiley_x*$locations_per_tile_x_count;
			$min_tiley_z__chunk_location_top = $min_tiley_z*$locations_per_tile_z_count;
			$max_tiley_z__chunk_location_bottom = $max_tiley_z*$locations_per_tile_z_count+$locations_per_tile_z_count;
			
			while ($min_tiley_x__chunk_location_right>$camera_left) {
				$min_tiley_x -= 1;
				$min_tiley_x__chunk_location_right = $min_tiley_x*$locations_per_tile_x_count+$locations_per_tile_x_count;
			}
			while ($max_tiley_x__chunk_location_left<$camera_right) {
				$max_tiley_x += 1;
				$max_tiley_x__chunk_location_left = $max_tiley_x*$locations_per_tile_x_count;
			}
			while ($min_tiley_z__chunk_location_top>$camera_bottom) {
				$min_tiley_z -= 1;
				$min_tiley_z__chunk_location_top = $min_tiley_z*$locations_per_tile_z_count;
			}
			while ($max_tiley_z__chunk_location_bottom<$camera_top) {
				$max_tiley_z += 1;
				$max_tiley_z__chunk_location_bottom = $max_tiley_z*$locations_per_tile_z_count+$locations_per_tile_z_count;
			}
			
			$tile_x_count = $max_tiley_x-$min_tiley_x+1;
			$tile_z_count = $max_tiley_z-$min_tiley_z+1;	
			$si_yml_path = "$chunkymapdata_thisworld_path/singleimage.yml";
			$si_metadata = null;
			
			$si_left = null;
			$si_top = null;
			$si_w = null;
			$si_h = null;
			$si_bottom = null;
			$si_right = null;
			if (is_file($si_yml_path)) {
				$si_metadata = get_dict_from_conf($si_yml_path, ":");
				if ($si_metadata!==null) {
					if (isset($si_metadata["image_top"]) and isset($si_metadata["image_bottom"])) {
						if ($si_metadata["image_top"]<$si_metadata["image_bottom"]) {
							$cartesian_bottom = $si_metadata["image_top"];
							$si_metadata["image_top"] = $si_metadata["image_bottom"];
							$si_metadata["image_bottom"] = $cartesian_bottom;
						}
					}
					if (isset($si_metadata["image_left"])) { $si_left=$si_metadata["image_left"]; }
					if (isset($si_metadata["image_top"])) { $si_top=$si_metadata["image_top"]; }
					if (isset($si_metadata["image_w"])) { $si_w=$si_metadata["image_w"]; }
					if (isset($si_metadata["image_h"])) { $si_h=$si_metadata["image_h"]; }
					if (isset($si_metadata["image_bottom"])) {
						$si_bottom = $si_metadata["image_bottom"];
					}
					elseif (isset($si_metadata["image_top"]) and isset($si_metadata["image_h"])) {
						$si_bottom=$si_top-$si_h; //minus since cartesian (which is assured above)
					}
					if (isset($si_metadata["image_right"])) {
						$si_right = $si_metadata["image_right"];
					}
					elseif (isset($si_metadata["image_left"]) and isset($si_metadata["image_w"])) {
						$si_right=$si_left+$si_w;
					}
				}
			}
			
			$markers = get_markers_from_dir($chunkymapdata_thisworld_path."/markers");
			$players = get_markers_from_dir($chunkymapdata_thisworld_path."/players");
			$index = 0;
			$players_count = count($players);
			while ($index<$players_count) {
				$this_player = $players[$index];
				$img_src = "$chunkymapdata_thisworld_path/players/singleplayer.png";
				if (!isset($players[$index]["image"])) {
					$players[$index]["image"] = $img_src;
				}
				if (isset($players[$index]["image"])) {
					if (isset($players[$index]["index"])) {
						$public_index=$players[$index]["index"];
						$players[$index]["img_id"] = "player"."$public_index"."_img";
						//echo ("players[index][img_id]:".$players[$index]["img_id"]);
					}
					else {
						echo_error("Missing index for player\r\n");
					}
				}
				else {
					echo echo_error("Missing image for player\r\n");
				}
				$index++;
			}
			//echo ("finished adding id to $players_count player(s)\r\n");
			//img_id is actually only needed for canvas drawing
			$index = 0;
			$markers_count = count($markers);
			while ($index<$markers_count) {
				if (isset($markers[$index]["image"])) {
					if (isset($markers[$index]["index"])) {
						$public_index=$markers[$index]["index"];
						$markers[$index]["img_id"] = "marker"."$public_index"."_img";
					}
					else {
						echo_error("Missing index for marker "+$markers[$index]["name"]);
					}
				}
				$index++;
			}
			//images are echoed further down
			
			
			if ($html4_mode_enable!==true) {
			//image-rendering: -moz-crisp-edges; image-rendering:-o-crisp-edges; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges; -ms-interpolation-mode: nearest-neighbor;
				echo '<canvas id="myCanvas"></canvas> ';
				echo '<script>
					var my_canvas = document.getElementById("myCanvas");
					var x='.$x.';
					var z='.$z.';
					var zoom='.$zoom.';
					//var default_player_img = document.getElementById("singleplayer_img");';
					
					$player_count = count($players);
					echo '
					//var player_count='.$player_count.';
					var players=[';
					$index=0;
					while ($index<$player_count) {
						echo "{";
						$this_player = $players[$index];
						//if (isset($this_player["index"])) {
						$public_index = $this_player["index"];
						//}
						echo "x:".$this_player["x"].",\r\n";
						echo "z:".$this_player["z"].",\r\n";
						if (($show_player_names_enable===true) and isset($this_player["name"])) {
							echo "name:\"".$this_player["name"]."\",\r\n";
						}
						else {
							echo "name:null,\r\n";
						}
						if (isset($this_player["img_id"])) {
							echo "img_id:\"".$this_player["img_id"]."\",\r\n";
							echo "img_enable:true,\r\n";
						}
						else {
							echo "img_enable:false,\r\n";
						}
						echo "is_expired:".get_javascript_bool_value($this_player["is_expired"]).",\r\n";
						echo "is_idle:".get_javascript_bool_value($this_player["is_idle"]).",\r\n";
						echo "index:$public_index\r\n";
						echo "}";
						$index++;
						if ($index!=$player_count) {
							echo ",";
						}
						echo "\r\n";
					}
					echo '];'."\r\n";
					
					$marker_count = count($markers);
					echo '
					//var marker_count='.$marker_count.';
					var markers=[';
					$index=0;
					while ($index<$marker_count) {
						echo "{";
						$this_marker = $markers[$index];
						//if (isset($this_marker["index"])) {
						$public_index = $this_marker["index"];
						//}
						echo "x:".$this_marker["x"].",\r\n";
						echo "z:".$this_marker["z"].",\r\n";
						if (isset($this_marker["name"])) {
							echo "name:\"".$this_marker["name"]."\",\r\n";
						}
						else {
							echo "name:null,\r\n";
						}
						if (isset($this_marker["img_id"])) {
							echo "img_id:\"".$this_marker["img_id"]."\",\r\n";
							echo "img_enable:true,\r\n";
						}
						else {
							echo "img_enable:false,\r\n";
						}
						echo "is_expired:".get_javascript_bool_value($this_marker["is_expired"]).",\r\n";
						echo "is_idle:".get_javascript_bool_value($this_marker["is_idle"]).",\r\n";
						echo "index:$public_index\r\n";
						echo "}";
						$index++;
						if ($index!=$marker_count) {
							echo ",";
						}
						echo "\r\n\r\n";
					}
					echo '];
					
					var chunkymap_view_max_zoom='.$chunkymap_view_max_zoom.';
					var chunkymap_view_min_zoom='.$chunkymap_view_min_zoom.';
					var chunkymap_zoom_delta='.$chunkymap_change_zoom_multiplier.';
					var chunks_enable='.get_javascript_bool_value($chunks_enable).';
					var visual_debug_enable='.get_javascript_bool_value($visual_debug_enable).';
					var chunks_per_tile_x_count='.$chunks_per_tile_x_count.';
					var chunks_per_tile_z_count='.$chunks_per_tile_z_count.';
					var tile_w='.$tile_w.';
					var tile_h='.$tile_h.';
					var si_left='.get_javascript_int_value($si_left).';
					var si_top='.get_javascript_int_value($si_top).';
					var si_w='.get_javascript_int_value($si_w).';
					var si_h='.get_javascript_int_value($si_h).';
					var si_bottom='.get_javascript_int_value($si_bottom).';
					var si_right='.get_javascript_int_value($si_right).';
					var EM_PER_WIDTH_COUNT = '.$EM_PER_WIDTH_COUNT.';
					var size_1em_pixel_count = null;
					var font_string = null;
					//var ctx = my_canvas.getContext("2d");
					//ctx.canvas.width = window.innerWidth;
					//ctx.canvas.height = window.innerHeight;
					//ctx.fillStyle = "rgb(r,g,b)";
					var size_1pt_pixel_count = null;
					var padding_w = null;
					var padding_h = null;
					var pen_x = null;
					var camera_w = null; //calculated below
					var camera_h = null; //calculated below
					var camera_left = null; //calculated below
					var camera_top = null; //calculated below
					var camera_right = null; //calculated below
					var camera_bottom = null; //calculated below
					var current_w = null;
					var current_h = null;
					var current_ratio = null;
					var zoom_in_button_index = null;
					var zoom_out_button_index = null;
					var zoom_out_label_index = null;
					var xy_label_index = null;
					var xy_label = null;
					var zoom_label = null;
					var zoom_in_button = null;
					var zoom_out_button = null;
					var label0 = null;
					var label1 = null;
					var label2 = null;
					var label3 = null;
					var label4 = null;
					var label5 = null;
					var canvas_offset_x = 0;
					var canvas_offset_y = 0;
					var is_mouse_down = false;
					var mouse_start_point = {x:-1, y:-1};
					var mouse_end_point = {x:-1, y:-1};
					var mouse_point = {x:-1, y:-1};
					var dragging_prev_point = {x:-1, y:-1};
					var zoomed_size_1pt_pixel_count = null;
					var ctx = null;
					
					ctx = my_canvas.getContext("2d");
					process_resize();
					ctx.fillStyle = "black";
					ctx.fillRect(0,0,ctx.canvas.width,ctx.canvas.height);
					var tmp_widget = {x:100,y:100,text:"Loading..."};
					draw_widget_recolored(tmp_widget, "rgb(128,128,128)");

					var powered_by_label_size_em = .75;
					var powered_by_label = create_bawidget(ctx.canvas.width/2, size_1em_pixel_count*powered_by_label_size_em, 0, 0, null, "powered_by_label");
					powered_by_label.text = "Chunkymap";
					powered_by_label.size_em = powered_by_label_size_em;
					//powered_by_label.color_string = "rgb(12,132,245)"
					powered_by_label.color_string = "rgb(192,192,192)"
					
					function zoom_in() {
						zoom*=chunkymap_zoom_delta;
						process_zoom_change();  //DOES call process_view_change
						draw_map();
					}
					function zoom_out() {
						zoom/=chunkymap_zoom_delta;
						process_zoom_change();  //DOES call process_view_change
						draw_map();
					}
					function process_resize() {
						//var ctx = my_canvas.getContext("2d");
						ctx.canvas.width = window.innerWidth;
						ctx.canvas.height = window.innerHeight;
						current_w = ctx.canvas.width;
						current_h = ctx.canvas.height;
						//current_w = window.innerWidth;
						//current_h = window.innerHeight;
						current_ratio = current_w/current_h;
						
						if (ctx.canvas.height>ctx.canvas.width) {
							size_1em_pixel_count = Math.round(ctx.canvas.height/EM_PER_WIDTH_COUNT);
						}
						else {
							size_1em_pixel_count = Math.round(ctx.canvas.width/EM_PER_WIDTH_COUNT);
						}
						if (powered_by_label!=null) {
							//powered_by_label.y = ctx.canvas.height-size_1em_pixel_count;
							powered_by_label.y = size_1em_pixel_count/2;
						}
						font_string = Math.round(size_1em_pixel_count)+"px Calibri";
						size_1pt_pixel_count = size_1em_pixel_count/16;
						padding_w = Math.round(size_1em_pixel_count/3.0);
						padding_h = Math.round(size_1em_pixel_count/3.0);
						canvas_offset_x = my_canvas.offsetLeft; //or ctx.canvas.offsetLeft;  //or ?
						canvas_offset_y = my_canvas.offsetTop; //or ctx.canvas.offsetTop;  //or ?
						process_zoom_change();  //DOES call process_view_change
					}
					function process_view_change() {
						//NOTE: this should be exactly the same math as php uses to make sure there are the same #of tiles displayed as were loaded by php
						if (ctx.canvas.width>ctx.canvas.height) { //if (current_w>current_h) {
							camera_w = (800) * (1.0/zoom);
							camera_h = camera_w/current_ratio;
						}
						else {
							camera_h = (800) * (1.0/zoom);
							camera_w = camera_h*current_ratio;
						}
						camera_left = x - (camera_w/2.0);
						camera_top = z + (camera_h/2.0); //plus since cartesian
						camera_right = camera_left+camera_w;
						camera_bottom = camera_top - camera_h; //minus since cartesion
						if (label4!=null) {
							//change_widget(label4, "[4] camera_w: "+Math.round(camera_w)+"; camera_h:"+Math.round(camera_h))
						}
					}
					function process_zoom_change() {
						var zoom_in_img = null;
						var zoom_out_img = null;
						var zoom_in_img_disabled = null;
						var zoom_out_img_disabled = null;
						var tmp_zoom_out_ptr = zoom_out;
						var tmp_zoom_in_ptr = zoom_in;
						
						if (zoom<chunkymap_view_min_zoom) {zoom = chunkymap_view_min_zoom;}
						if (zoom>chunkymap_view_max_zoom) {zoom = chunkymap_view_max_zoom;}
						
						if (zoom==chunkymap_view_min_zoom) {
							zoom_out_img = document.getElementById("zoom_out_disabled");
							tmp_zoom_out_ptr = null;
						}
						else {
							zoom_out_img = document.getElementById("zoom_out");
						}
						if (zoom==chunkymap_view_max_zoom) {
							zoom_in_img = document.getElementById("zoom_in_disabled");
							tmp_zoom_in_ptr = null;
						}
						else {
							zoom_in_img = document.getElementById("zoom_in");
						}
						if (xy_label!=null) {
							xy_label.text = Math.round(x)+","+Math.round(z);
						}
						
						zoom_label_value=zoom*100;
						if (zoom_label_value>1) {
							zoom_label_value = Math.round(zoom_label_value, 1);
						}
						else {
							zoom_label_value = Math.round(zoom_label_value, 7);
						}
						zoomed_size_1pt_pixel_count = size_1pt_pixel_count*zoom;
						if (zoom_label!=null) {
							change_widget(zoom_label, zoom_label_value+"%");
							//zoom_label.text=zoom_label_value+"%";
						}
						if (label3!=null) {
							//change_widget(label3, "size_1pt_pixel_count:"+size_1pt_pixel_count+"  zoomed_size_1pt_pixel_count:"+zoomed_size_1pt_pixel_count);
						}
						
						if (zoom_in_button!=null) {
							zoom_in_button.click_event=tmp_zoom_in_ptr;
							zoom_in_button.image=zoom_in_img;
						}
						if (zoom_out_button!=null) {
							zoom_out_button.click_event=tmp_zoom_out_ptr;
							zoom_out_button.image=zoom_out_img;
						}
						process_view_change();
					}
					
					function get_world_point_from_screen_point(screen_point) {
						horz_ratio = screen_point.x/current_w;
						vert_ratio = screen_point.y/current_h;
						inverse_vert_ratio = 1.0 - vert_ratio;
						return {
							x:camera_left+horz_ratio*camera_w,
							z:camera_bottom+inverse_vert_ratio*camera_h
						};
					}
					
					function get_screen_point_from_world_coords(location_x, location_z) {					
						//var half_camera_w = camera_w/2.0;
						//var half_camera_h = camera_h/2.0;
						//subtract camera coords first (subtract both coords since location and camera are both cartesian)
						horz_ratio = (location_x-camera_left)/(camera_right-camera_left);
						vert_ratio = (location_z-camera_top)/(camera_bottom-camera_top);
						return {
							x:horz_ratio*current_w,
							y:vert_ratio*current_h
						};
					}
					
					//size_em: size_width_keeping_aspect_this_many_em
					function draw_markers(this_list, size_em, default_color_string) {
						is_debug_shown = false;
						var debug_adjustment = 1.345; //TODO: debug--why is this needed?
						for (i=0; i<this_list.length; i++) {
							this_marker = this_list[i];
							screen_point = get_screen_point_from_world_coords(this_marker.x, this_marker.z);
							var pen_x = 0;
							var pen_y = 0;
							var w = size_em*size_1em_pixel_count;
							
							if (w<zoomed_size_1pt_pixel_count) {
								w = zoomed_size_1pt_pixel_count;
							}
							if (this_marker.img_enable) {
								this_image = document.getElementById(this_marker.img_id);
								if (this_image.width>32) {
									w = this_image.width*zoomed_size_1pt_pixel_count*debug_adjustment;
								}
								var h = w*(this_image.height/this_image.width);
								ctx.drawImage(this_image, screen_point.x-w/2.0, screen_point.y-h/2.0, w, h);
								//pen_y += h;
								pen_x += w/2;
							}
							else {
								
								var radius = w/4.0;
								ctx.beginPath();
								ctx.arc(screen_point.x, screen_point.y, radius, 0, 2 * Math.PI, false);
								//ctx.fillStyle = \'white\';
								ctx.fillStyle = default_color_string;
								ctx.fill();
								ctx.lineWidth = size_1pt_pixel_count;
								ctx.strokeStyle = \'#003300\';
								ctx.stroke();							
								pen_x += w;
								pen_y += radius;
							}
							
							if (this_marker.name!=null) {
								if (!is_debug_shown) {
									if ((this_marker.name!="singleplayer") || (i==(this_list.length-1)) ) {
										//change_widget(label1, "recent marker: "+this_marker.name+" at x"+Math.round(this_marker.x)+",z"+Math.round(this_marker.z)+" (screen "+Math.round(screen_point.x)+","+Math.round(screen_point.y)+")");
										is_debug_shown = true;
									}
								}
								ctx.font = font_string;
								ctx.strokeStyle="rgb(0,0,0)";
								ctx.lineWidth= size_1pt_pixel_count*3;
								ctx.strokeText(this_marker.name, screen_point.x+pen_x, screen_point.y+pen_y+size_1em_pixel_count/2);
								ctx.fillStyle = "rgb(255,255,255)";
								if (this_marker.is_expired) {
									ctx.fillStyle = "rgb(255,0,0)";
									ctx.globalAlpha = .33;
								}
								else if (this_marker.is_idle) {
									ctx.globalAlpha = .5;
								}
								ctx.fillText(this_marker.name, screen_point.x+pen_x, screen_point.y+pen_y+size_1em_pixel_count/2);
								ctx.globalAlpha = 1.0;
							}
						}
					}
					
					var bw_count = 0;
					var bawidgets = new Array();
					var last_bawidget = null;
					
					
					function create_bawidget(at_x, at_y, width, height, this_onclick, name) {
						this_widget = Array();
						this_widget.color_string = "rgb(255,255,255)";
						this_widget.size_em=1.0;
						this_widget.visible = true;
						this_widget.x = at_x;
						this_widget.y = at_y;
						this_widget.width = width;
						this_widget.height = height;
						this_widget.click_event = this_onclick;
						this_widget.name = name;
						this_widget.image = null;
						this_widget.text = null;
						return this_widget;
					}
					
					function add_bawidget(at_x, at_y, width, height, this_onclick, name) {
						this_widget = create_bawidget(at_x, at_y, width, height, this_onclick, name);
						bawidgets[bw_count] = this_widget;
						last_bawidget = this_widget;
						bw_count++;
					}
					function contains_coords(bawidget, cursor_x, cursor_y) {
						right = bawidget.x+bawidget.width;
						bottom = bawidget.y+bawidget.height;
						return cursor_x>=bawidget.x && cursor_y>=bawidget.y && cursor_x<right && cursor_y<bottom;
					}
					function click_if_contains(bawidget, cursor_x, cursor_y) {
						if (contains_coords(bawidget, cursor_x, cursor_y)) {
							if (bawidget.click_event != null) {
								bawidget.click_event();
							}
						}
					}
					
					
					
					
					function draw_map() {
						
						var r = 0; //border
						var g = 0; //exists
						var b = 0; //
						
						var alert_string="";
						if (current_ratio==null) {
							alert_string+="current_ratio is null; ";
						}
						if (font_string==null) {
							alert_string+="font_string is null; ";
						}
						if (current_w==null) {
							alert_w+="current_ratio is null; ";
						}
						if (current_w==null) {
							alert_w+="current_ratio is null; ";
						}
						if (current_ratio==null) {
							alert_string+="current_ratio is null; ";
						}
						if (alert_string.length>0) {
							alert(alert_string);
						}
						
						
						process_resize();
						
						ctx.fillStyle = "black";
						ctx.fillRect(0,0,ctx.canvas.width,ctx.canvas.height);
						
						//ctx.fillStyle = "white";
						//ctx.rect(20,20,150,100);
						//ctx.stroke(); 
						
						//size_1pt_pixel_count = ctx.canvas.height/600.0;
						var bw_index = 0;
						
						var si = document.getElementById("singleimage");
						if ((si!==null)&&(si_left!==null)&&(si_top!==null)&&(si_w!==null)&&(si_h!==null)) {
							
							si_canvas_topleft = get_screen_point_from_world_coords(si_left, si_top);
							si_canvas_bottomright = get_screen_point_from_world_coords(si_right, si_bottom);
							si_canvas_w = si_canvas_bottomright.x - si_canvas_topleft.x;
							si_canvas_h = si_canvas_bottomright.y - si_canvas_topleft.y;
							
							ctx.drawImage(si, si_canvas_topleft.x, si_canvas_topleft.y, si_canvas_w, si_canvas_h);
							//label5.text = "--map "+si_canvas_topleft.x+":"+si_canvas_bottomright.x+","+si_canvas_topleft.y+":"+si_canvas_bottomright.y+" "+si_canvas_w+"x"+si_canvas_h+" --camera "+camera_left+":"+camera_right+","+camera_bottom+":"+camera_top;
							//label5.text = "map world bounds: "+si_left+":"+si_right+","+si_bottom+":"+si_top;
							//label1.text = "map on canvas "+Math.round(si_canvas_topleft.x)+":"+Math.round(si_canvas_bottomright.x)+","+Math.round(si_canvas_topleft.y)+":"+Math.round(si_canvas_bottomright.y)+" "+Math.round(si_canvas_w)+"x"+Math.round(si_canvas_h);
							//label2.text="[2] camera: "+Math.round(camera_left)+":"+Math.round(camera_right)+","+Math.round(camera_bottom)+":"+Math.round(camera_top);
							//UNUSED (or mouse screen position): label4.text="canvas "+current_w+"x"+current_h;
						}
						draw_markers(markers, 1, "rgb(71,219,37)");
						draw_markers(players, .7, "white");
						for (i=0; i<bawidgets.length; i++) {
							draw_widget(bawidgets[i]);
						}
						draw_widget(powered_by_label);
					}//end draw map
					
					function change_widget(this_widget, new_text) {
						//draw_widget_recolored(this_widget, "rgb(64,64,64)");
						ctx.fillStyle="rgb(0,0,0)";
						if (this_widget.text != null) {
							text_h = size_1em_pixel_count*this_widget.size_em;
							ctx.fillRect(this_widget.x, this_widget.y-size_1em_pixel_count*this_widget.size_em+text_h/4, this_widget.text.length*size_1em_pixel_count*this_widget.size_em/2.0, text_h);
						}
						this_widget.text = new_text;
						draw_widget_recolored(this_widget, this_widget.color_string);
					}
					
					function draw_widget(this_widget) {
						draw_widget_recolored(this_widget, this_widget.color_string);
					}
					
					
					
					function draw_widget_recolored(this_widget, color_string) {
						if (this_widget.visible) {
							if (this_widget.text != null) {
								//ctx.font = font_string;
								ctx.font = Math.round(this_widget.size_em*size_1em_pixel_count)+"px Calibri";
								ctx.fillStyle = color_string;
								ctx.fillText(this_widget.text, this_widget.x, this_widget.y);
							}
							if (this_widget.image != null) {
								ctx.drawImage(this_widget.image, this_widget.x, this_widget.y, this_widget.width, this_widget.height);
							}
						}
					}
					
					function do_end_drag() {
						dragging_prev_point.x=-1;
						dragging_prev_point.y=-1;
					}

					// var handle_mousemove = function (e) {
						// mouse_point.x = parseInt(e.clientX-my_canvas.offsetLeft);
						// mouse_point.y = parseInt(e.clientY-my_canvas.offsetTop);
						// mouse_point = get_relative_mouse_point(e);
						
						
						// world_point = get_world_point_from_screen_point(mouse_point);
						// if (is_mouse_down) {
							// label0.text = mouse_point.x+","+mouse_point.y+" mousemove ";
							// label0.text += " is_mouse_down=True"
							// if (dragging_prev_point.x>-1 && dragging_prev_point.y>-1) {
								// x += (mouse_point.x - dragging_prev_point.x)/zoomed_size_1pt_pixel_count;
								// z -= (mouse_point.x - dragging_prev_point.x)/zoomed_size_1pt_pixel_count;
								// process_view_change();
							// }
							// dragging_prev_point.x=mouse_point.x;
							// dragging_prev_point.y=mouse_point.y;
							// draw_map();
						// }
						// else {
							// change_widget(label0, mouse_point.x+","+mouse_point.y+" world_point: "+world_point.x+","+world_point.z);
						// }
					// }
					var handle_mousedown = function(e) {
						//var xOffset=Math.max(document.documentElement.scrollLeft,document.body.scrollLeft);
						//var yOffset=Math.max(document.documentElement.scrollTop,document.body.scrollTop);
						//mouse_point.x = parseInt(e.clientX+xOffset-my_canvas.offsetLeft);
						//mouse_point.y = parseInt(e.clientY+yOffset-my_canvas.offsetTop);
						mouse_point = get_relative_mouse_point(e);
						is_mouse_down = true;
						//change_widget(label0, mouse_point.x+","+mouse_point.y+" mouse down");
					}
					var handle_mouseup = function(e) {
						is_mouse_down = false;
						do_end_drag();
						//change_widget(label0, "mouse released");
						//label0.text="mouse released";
						//draw_map();
					}
					handle_mouseout = function (e) {
						is_mouse_down = false;
						do_end_drag();
						//change_widget(label0, "(cursor is outside of window)");
						change_widget(label0, "");
						//label0.text="mouse left window";
						draw_map();
					}
					
					//function getMousePos(canvas, e) {
					//	var rect = canvas.getBoundingClientRect();
					//	return {
					//			x: e.clientX - rect.left,
					//			y: e.clientY - rect.top
					//			};
					//}
					
					function get_relative_mouse_point(e) {
						//formerly get_mouse_point
						
						var xOffset=Math.max(document.documentElement.scrollLeft,document.body.scrollLeft);
						var yOffset=Math.max(document.documentElement.scrollTop,document.body.scrollTop);
						return {
						x:parseInt(e.clientX+xOffset-my_canvas.offsetLeft),
						y:parseInt(e.clientY+yOffset-my_canvas.offsetTop)
						};
						//return {
						//x:parseInt(e.clientX+xOffset),
						//y:parseInt(e.clientY+yOffset)
						//};
					}
					
					window.onload = function() {
						//my_canvas = document.getElementById("myCanvas");
						//my_canvas.onclick = function(event) {
						//	for (i=0; i<bawidgets.length; i++) {
						//		click_if_contains(bawidgets[i], event.clientX, event.clientY);
						//	}
						//};
						
						//my_canvas.addEventListener("mousemove", handle_mousemove, false);
						my_canvas.addEventListener("mousedown", handle_mousedown, false);
						my_canvas.addEventListener("mouseup", handle_mouseup, false);
						my_canvas.addEventListener("mouseout", handle_mouseout, false);
						my_canvas.addEventListener("mousemove", function(e) {
							//var xOffset=Math.max(document.documentElement.scrollLeft,document.body.scrollLeft);
							//var yOffset=Math.max(document.documentElement.scrollTop,document.body.scrollTop);
							//mouse_point.x = parseInt(e.clientX+xOffset-my_canvas.offsetLeft);
							//mouse_point.y = parseInt(e.clientY+yOffset-my_canvas.offsetTop);
							mouse_point = get_relative_mouse_point(e);
							//var this_text = "on your screen: "+mouse_point.x+","+mouse_point.y+" mousemove";
							//change_widget(label4, this_text);
							
							
							world_point = get_world_point_from_screen_point(mouse_point);
							if (is_mouse_down) {
								if (dragging_prev_point.x>-1 && dragging_prev_point.y>-1) {
									//flip both axes to give the effect of moving the map instead of the camera:
									prev_cursor_world_point = get_world_point_from_screen_point(dragging_prev_point);
									cursor_world_point = get_world_point_from_screen_point(mouse_point);
									x -= cursor_world_point.x - prev_cursor_world_point.x;
									z -= cursor_world_point.z - prev_cursor_world_point.z;
									//(z was already flipped [cartesian] so flip again):
									//x -= (mouse_point.x - dragging_prev_point.x)/zoomed_size_1pt_pixel_count;
									//z += (mouse_point.y - dragging_prev_point.y)/zoomed_size_1pt_pixel_count;
									process_view_change();
								}
								dragging_prev_point.x=mouse_point.x;
								dragging_prev_point.y=mouse_point.y;
								draw_map();
							}
							else {
								//change_widget(label0, mouse_point.x+","+mouse_point.y+" world_point: "+Math.round(world_point.x)+","+Math.round(world_point.z));
							}
							change_widget(label0, "location: "+Math.round(world_point.x)+","+Math.round(world_point.z));
						  }, false);
						//my_canvas.addEventListener("mousemove", function(evt) {
						//	var mousePos = getMousePos(my_canvas, evt);
						//	var message = "Mouse position: " + mousePos.x + "," + mousePos.y;
						//	label0.text = message;
						//	draw_map();
						//  }, false);
						my_canvas.addEventListener("click", function(e){
							relative_canvas_point = get_relative_mouse_point(e)
							for (i=0; i<bawidgets.length; i++) {
								click_if_contains(bawidgets[i], relative_canvas_point.x, relative_canvas_point.y);
							}
						});
						//my_canvas.addEventListener(\'mousemove\', handle_mousemove, false);
						//FAILS: my_canvas.onmousemove = handle_mousemove;
						//FAILS: my_canvas.onmousemove = function(event) {
						//	handle_mousemove(event);
						//};
						//my_canvas.mousedown = function(event) {
						//	handle_mousedown(event);
						//};
						//my_canvas.mouseup = function(event) {
						//	handle_mouseup(event);
						//};
						//my_canvas.mouseout = function(event) {
						//	handle_mouseout(event);
						//};
							
						//ctx = my_canvas.getContext("2d");
						process_resize();
						
						var pen_x = size_1em_pixel_count;
						var pen_y = size_1em_pixel_count;
						var tmp_w = null;
						var tmp_h = null;
						var compass_rose_w = size_1em_pixel_count*5;
						
						//LOCATION LABEL (no click):
						bw_index = add_bawidget(pen_x+compass_rose_w/4, pen_y, tmp_w, tmp_h, null, "xy_label");
						xy_label = last_bawidget;
						xy_label.visible = false;
						//done on each draw: last_bawidget.text = 
						
						pen_y += size_1em_pixel_count + padding_h;
						
						//COMPASS ROSE (no click):
						var compass_rose_img = document.getElementById("compass_rose");
						var this_h_ratio = compass_rose_img.height/compass_rose_img.width;
						tmp_w = compass_rose_w;
						tmp_h = tmp_w*this_h_ratio;
						bw_index = add_bawidget(pen_x-padding_w, pen_y, tmp_w, tmp_h, null, "compass_rose");
						last_bawidget.image = compass_rose_img;
						compass_rose_img.style.visibility="hidden";
						pen_y += last_bawidget.height+padding_h;
						
						//ZOOM LABEL (no click):
						bw_index = add_bawidget(pen_x+compass_rose_w/5, pen_y, tmp_w, tmp_h, null, "zoom_label");
						zoom_label = last_bawidget;
						//done on each draw: last_bawidget.text = (zoom*100)+"%"
						pen_y += size_1em_pixel_count + padding_h;

						//ZOOM IN:
						var zoom_in_img = document.getElementById("zoom_in");
						this_h_ratio = zoom_in_img.height/zoom_in_img.width;
						tmp_w = size_1em_pixel_count*2;
						tmp_h = tmp_w*this_h_ratio;
						bw_index = add_bawidget(pen_x, pen_y, tmp_w, tmp_h, null, "zoom_in", null);
						//zoom_in_button_index = bw_index;
						zoom_in_button = last_bawidget;
						last_bawidget.image=zoom_in_img;
						zoom_in_img.style.visibility="hidden";
						document.getElementById("zoom_in_disabled").style.visibility="hidden";
						//pen_y += tmp_h+padding_h;
						pen_x += tmp_w;
						
						//ZOOM OUT
						var zoom_out_img = document.getElementById("zoom_out");
						this_h_ratio = zoom_out_img.height/zoom_out_img.width;
						tmp_w = size_1em_pixel_count*2;
						tmp_h = tmp_w*this_h_ratio;
						bw_index = add_bawidget(pen_x, pen_y, tmp_w, tmp_h, null, "zoom_out", null);
						zoom_out_button = last_bawidget;
						//zoom_out_button_index = bw_index;
						last_bawidget.image=zoom_out_img;
						zoom_out_img.style.visibility="hidden";
						document.getElementById("zoom_out_disabled").style.visibility="hidden";
						pen_y += tmp_h+size_1em_pixel_count+padding_h;
						pen_x -= tmp_w;			

						//label0 (no click):
						bw_index = add_bawidget(pen_x, pen_y, tmp_w, tmp_h, null, "label0");
						label0 = last_bawidget;
						//done on each draw: last_bawidget.text = 
						pen_y += size_1em_pixel_count + padding_h;

						//label1 (no click):
						bw_index = add_bawidget(pen_x, pen_y, tmp_w, tmp_h, null, "label1");
						label1 = last_bawidget;
						//done on each draw: last_bawidget.text = 
						pen_y += size_1em_pixel_count + padding_h;

						//label2 (no click):
						bw_index = add_bawidget(pen_x, pen_y, tmp_w, tmp_h, null, "label2");
						label2 = last_bawidget;
						//done on each draw: last_bawidget.text = 
						pen_y += size_1em_pixel_count + padding_h;

						//label3 (no click):
						bw_index = add_bawidget(pen_x, pen_y, tmp_w, tmp_h, null, "label3");
						label3 = last_bawidget;
						//done on each draw: last_bawidget.text = 
						pen_y += size_1em_pixel_count + padding_h;

						//label4 (no click):
						bw_index = add_bawidget(pen_x, pen_y, tmp_w, tmp_h, null, "label4");
						label4 = last_bawidget;
						//done on each draw: last_bawidget.text = 
						pen_y += size_1em_pixel_count + padding_h;

						//label5 (no click):
						bw_index = add_bawidget(pen_x, pen_y, tmp_w, tmp_h, null, "label5");
						label5 = last_bawidget;
						//done on each draw: last_bawidget.text = 
						pen_y += size_1em_pixel_count + padding_h;
						
						chunkymap_table = document.getElementById("chunkymap_table");
						if (chunkymap_table!=null) {
							chunkymap_table.style.visibility="hidden";
						}
						singleimage_table = document.getElementById("singleimage_table");
						if (singleimage_table!=null) {
							singleimage_table.style.visibility="hidden";
						}
						
						process_zoom_change();
						draw_map();
					}
					</script>
					';
			}//end if not $html4_mode_enable
			global $td_decachunk_placeholder_content;
			global $td_chunk_placeholder_content;
			$td_tile_placeholder_content = null;
			if ($chunks_enable) {
				$td_tile_placeholder_content = $td_chunk_placeholder_content;
			}
			else {
				$td_tile_placeholder_content = $td_decachunk_placeholder_content;
			}
			
			
			$si_path = "$chunkymapdata_thisworld_path/singleimage.jpg";
			$si_yml_path = "$chunkymapdata_thisworld_path/singleimage.yml";
			if (is_file($si_path) and is_file($si_yml_path)) {
				$style_append="";
				if ($html4_mode_enable===true) {
					echo '<table id="singleimage_table" style="width:100%'."$style_append".'">'."\r\n";
				}
				else {
					$style_append="; visibility:hidden";
					echo '<table id="singleimage_table" style="position:absolute; top:0px; left:0px; width:0px; height:0px'."$style_append".'">'."\r\n";
				}
				echo '  <tr><td style="background-image:url(\'chunkymapdata/images/loading.png\'); background-repeat: no-repeat; background-size: 100% 100%">'."\r\n";
				$style_append="";
				$players_count = count($players);
				$index=0;
				while ($index<$players_count) {
					$this_player = $players[$index];
					$public_index = $this_player["index"];
					// z-index:999; 
					$zoomed_head_w="1%";
					$img_style="";
					$img_border_style="border: 1px solid white;";
					$text_style="color:white;";
					$img_id = null;
					$img_enable = true;
					$img_src = "$chunkymapdata_thisworld_path/players/singleplayer.png";
					if (!isset($this_player["image"])) {
						$this_player["image"] = $img_src;
					}
					if (isset($this_player["image"])) {
						$img_src = $this_player["image"];
						if (isset($this_player["img_id"])) { //this is only needed for changing canvas drawing location via ajax
							$img_id = $this_player["img_id"];
							$img_enable = true;
						}
						else {
							echo "missing player img_id\r\n";
						}
					}
					else {
						echo "missing player image\r\n";
					}
					//$text = "$public_index";
					$text = "";
					if ($show_player_names_enable) {
						if (isset($this_player["name"])) {
							$text = $this_player["name"];
						}
					}
					//if ($this_player["is_expired"]===true) { //should only be used for debug
					//	$img_border_style="border: 1px solid rgba(128,128,128,.5);";
					//	$img_style.="opacity: 0.1; filter: alpha(opacity=10);";  //filter is for IE8 and below
					//	$text_style="color:white; opacity: 0.4; filter: alpha(opacity=40);";   //filter is for IE8 and below
					//	$text.=" (expired)";
					//}
					//elseif
					if ($this_player["is_idle"]===true) {
						$img_border_style="border: 1px solid rgba(128,128,128,.5);";
						$img_style.="opacity: 0.4; filter: alpha(opacity=40);";  //filter is for IE8 and below
						$text_style="color:white; opacity: 0.4; filter: alpha(opacity=40);";   //filter is for IE8 and below
					}
					
					$rel_x = "50%"; //TODO: NOT YET IMPLEMENTED (determine from actual location)
					$rel_z = "50%"; //TODO: NOT YET IMPLEMENTED (determine from actual location)
					
					echo "    <div style=\"position:absolute; left:$rel_x; top:$rel_z; width: $zoomed_head_w; $img_border_style\">\r\n";
					if ($img_enable===true) {
						$id_string = "";
						if ($img_id!==null) {
							$id_string=" id=\"$img_id\"";
						}
						echo "      <img$id_string src=\"$img_src\" style=\"$img_style\"/>\r\n";
					}
					echo "      <span style=\"$text_style\">$text</span></div>\r\n";
					$index++;
				}//end for player
				
				$markers_count = count($markers);
				$index=0;
				echo "\r\n";
				while ($index<$markers_count) {
					$this_marker = $markers[$index];
					$public_index = $this_marker["index"];
					// z-index:999; 
					$zoomed_head_w="2%";
					$img_style="";
					$img_border_style="border: 1px solid white;";
					$text_style="color:white;";
					$img_id = "marker"."$public_index"."_img";
					$img_enable = false;
					$img_src = null;
					$text = "";
					if (isset($this_marker["image"])) {
						$img_enable = true;
						$img_src = $this_marker["image"];
					}
					else {
						$text = "$public_index";
					}
					if (isset($this_marker["name"])) {
						$text = $this_marker["name"];
					}
					//if ($this_marker["is_expired"]===true) { //should only be used for debug
					//	$img_border_style="border: 1px solid rgba(128,128,128,.5);";
					//	$img_style.="opacity: 0.1; filter: alpha(opacity=10);";  //filter is for IE8 and below
					//	$text_style="color:white; opacity: 0.4; filter: alpha(opacity=40);";   //filter is for IE8 and below
					//	$text.=" (expired)";
					//}
					//else
					if ($this_marker["is_idle"]===true) {
						$img_border_style="border: 1px solid rgba(128,128,128,.5);";
						$img_style.="opacity: 0.4; filter: alpha(opacity=40);";  //filter is for IE8 and below
						$text_style="color:white; opacity: 0.4; filter: alpha(opacity=40);";   //filter is for IE8 and below
					}
					
					$rel_x = "50%"; //TODO: NOT YET IMPLEMENTED (determine from actual location)
					$rel_z = "50%"; //TODO: NOT YET IMPLEMENTED (determine from actual location)
					
					echo "    <div style=\"position:absolute; left:$rel_x; top:$rel_z; width: $zoomed_head_w; $img_border_style\">\r\n";
					if ($img_enable===true) {
						echo "      <img id=\"$img_id\" src=\"$img_src\" style=\"$img_style\"/>\r\n";
					}
					echo "      <span style=\"$text_style\">$text</span></div>\r\n";
					$index++;
				}//end for marker
				echo '    <img id="singleimage" style="width:100%; $style_append" src="'."$si_path".'"/>'."\r\n";
				echo '  </td></tr>'."\r\n";
				echo '</table>'."\r\n";
			}
			else {
				echo '<--no '."$si_path".'-->'+"\r\n";
			}
			
			//echo "<img id=\"singleplayer_img\" src=\"$chunkymapdata_thisworld_path/players/singleplayer.png\" style=\"visibility:hidden\"/>";
			echo '<img id="compass_rose" src="chunkymapdata/images/compass_rose.png"/>';
			echo '<img id="zoom_in" src="chunkymapdata/images/zoom_in.png"/>';
			echo '<img id="zoom_in_disabled" src="chunkymapdata/images/zoom_in_disabled.png"/>';
			echo '<img id="zoom_out" src="chunkymapdata/images/zoom_out.png"/>';
			echo '<img id="zoom_out_disabled" src="chunkymapdata/images/zoom_out_disabled.png"/>';
			$this_tiley_z=$max_tiley_z; //start at max since screen is inverted cartesian
			if (($decachunks_enable==true) or ($chunks_enable==true)) {
				if ($visual_debug_enable!==true) {
					//this table loads the images then is hidden when javascript runs successfully, but it is also a map though not very functional
					if ($html4_mode_enable===true) {
						echo '<table id="chunkymap_table" cellspacing="0" cellpadding="0" style="width:100%">'."\r\n";
					}
					else {
						echo '<table id="chunkymap_table" cellspacing="0" cellpadding="0" style="position:absolute; top:0px; left:0px; width:0px; height:0px; visibility:hidden">'."\r\n";
					}
					echo '  <tr>'."\r\n";
					echo '    <td style="width:5%">'."$td_tile_placeholder_content".'</td>'."\r\n";
					echo "    <td style=\"width:95%\"><a href=\"?world_name=$world_name&zoom=$zoom&x=$x&z=".($z+($camera_h*$chunkymap_camera_pan_delta))."#chunkymap_top\">".'<img src="chunkymapdata/images/arrow_wide_up.png" style="width:90%"/>'.'</a></td>'."\r\n";
					echo '    <td style="width:5%">'."$td_tile_placeholder_content".'</td>'."\r\n";
					echo '  </tr>'."\r\n";
					$cell_perc=intval(round(100.0/$tile_x_count));
					echo '  <tr>'."\r\n";
					echo "    <td style=\"width:5%\"><a href=\"?world_name=$world_name&zoom=$zoom&x=".($x-($camera_w*$chunkymap_camera_pan_delta))."&z=$z#chunkymap_top\">".'<img src="chunkymapdata/images/arrow_wide_left.png" style="width:90%"/>'.'</a></td>'."\r\n";
					echo '    <td style="width:95%">'."\r\n";		
					echo '      <table id="chunk_table" cellpadding="0" cellspacing="0" style="width:100%">'."\r\n";
					while ($this_tiley_z>=$min_tiley_z) {
						$this_tiley_x=$min_tiley_x;
						echo "        <tr>\r\n";
						while ($this_tiley_x<=$max_tiley_x) {
							$img_path=null;
							echo "        <td>";
							if ($chunks_enable) {
								$img_path=get_chunk_image_path_from_chunky_coords($this_tiley_x, $this_tiley_z);
								if (!is_file($img_path)) {
									echo "<!-- no chunk $img_path -->";
									$img_path="chunkymapdata/images/chunk_blank.jpg";
								}
							}
							else {
								$img_path=get_decachunk_image_path_from_decachunk($this_tiley_x, $this_tiley_z);
								if (!is_file($img_path)) {
									echo "<!-- no decachunk $img_path -->";
									$img_path="chunkymapdata/images/decachunk_blank.jpg";
								}
							}
							echo "<img class=\"maptileimg\" src=\"$img_path\" style=\"width:100%\"/>"."</td>\r\n";
							$this_tiley_x++;
						}
						echo "        </tr>\r\n";
						$this_tiley_z-=1;
					}
					echo '      </table>';
					echo '    </td>'."\r\n";
					echo "    <td style=\"width:5%\"><a href=\"?world_name=$world_name&zoom=$zoom&x=".($x+($camera_w*$chunkymap_camera_pan_delta))."&z=$z#chunkymap_top\">".'<img src="chunkymapdata/images/arrow_wide_right.png" style="width:100%"/>'.'</a></td>'."\r\n";
					echo '  </tr>'."\r\n";
					echo '  <tr>'."\r\n";
					echo '    <td style="width:5%">'."$td_decachunk_placeholder_content".'</td>'."\r\n";
					echo "    <td style=\"width:90%\"><a href=\"?world_name=$world_name&zoom=$zoom&x=$x&z=".($z-($camera_h*$chunkymap_camera_pan_delta))."#chunkymap_top\">".'<img src="chunkymapdata/images/arrow_wide_down.png" style="width:100%"/>'.'</a></td>'."\r\n";
					echo '    <td style="width:5%">'."$td_decachunk_placeholder_content".'</td>'."\r\n";
					echo '  </tr>'."\r\n";
					echo '</table>'."\r\n";
				}
			}
			else {
				if ($html4_mode_enable===true) {
					//else see above for singleimage (if singleimage doesn't exist, this should run though)
					//echo 'There is nothing to do for html4_mode_enable since neither chunks nor decachunks were enabled (singleimage html4 is not yet implemented).';
				}
			}
			if ($html4_mode_enable===true) {
				echo '<center><small>Powered by <a href="https://github.com/expertmm/minetest-chunkymap">Chunkymap</a></small></center>';
			}
		}
		else { //not isset($world_name)
			echo "<h4>Choose world:</h4>";
			echo "<ul>";
			global $chunkymapdata_worlds_path;
			if ($chunkymapdata_handle = opendir($chunkymapdata_worlds_path)) {
				$append_vars="";
				if (isset($x)) {
					$append_vars.="&x=$x";
				}
				if (isset($z)) {
					$append_vars.="&z=$z";
				}
				if (isset($zoom)) {
					$append_vars.="&zoom=$zoom";
				}
				if (isset($chunkymap_anchor_name)) {
					$append_vars.="#$chunkymap_anchor_name";
				}
				global $chunkymap_anchor_name;
				while (false !== ($this_world_name = readdir($chunkymapdata_handle))) {
					if (substr($this_world_name, 0, 1) != ".") {
						$this_world_path = $chunkymapdata_worlds_path."/".$this_world_name;
						echo "<li><a href=\"?world_name=$this_world_name"."$append_vars#$chunkymap_anchor_name"."\">$this_world_name</a></li>";
					}
				}
				closedir($chunkymapdata_handle);
			}
			echo "</ul>";
		}
	}
	else {
		//error already shown by check_world()
	}
	
	//TODO: $zoom SHOULD BE interpreted so each block (pixel) is 1pt: 1066x600 pt canvas would have 66+2/3 blocks horizontally, is 37.5 blocks vertically
	//so, at zoom 1.0 canvas should show 60 chunks across (6 decachunks across)
}//end echo_chunkymap_canvas


function check_world() {
	global $chunkymapdata_thisworld_path;
	global $world_name;
	global $chunkymapdata_worlds_path;
	global $auto_choose_enable;
	global $show_missing_data_msg_enable;
	$non_world_world_count = 0;
	$world_count = 0;
	$non_world_world_name = null;
	$last_world_name = null;
	$is_ready = false;
	
	if (!isset($world_name)) {
		if (is_dir($chunkymapdata_worlds_path)) {
			if ($handle = opendir($chunkymapdata_worlds_path)) {
				while (false !== ($file_name = readdir($handle))) {
					if (substr($file_name, 0, 1) != ".") {
						$file_path = $chunkymapdata_worlds_path."/".$file_name;
						if (is_dir($file_path)) {
							//$world_name=$file_name;
							//break;
							if ($file_name!="world") {
								$non_world_world_name = $file_name;
								if ($auto_choose_enable===true) {
									$world_name = $file_name;
								}
								$non_world_world_count++;
							}
							$last_world_name = $file_name;
							$world_count++;
						}
					}
				}
				closedir($handle);
			}
		}
		else {
			if ($show_missing_data_msg_enable) {
				echo '<div style="color:red">There are no worlds in '."$chunkymapdata_worlds_path".' yet.</div>';
				echo '<div style="color:gray">Server owner should run singleimage.py to generate map, and generator.py to keep update players updated (only works with player files, <i>not player database which is optionally used by Minetest 0.4.16</i>)</div>';
				$show_missing_data_msg_enable = false;
			}
		}
		if ($world_count==1) {
			$world_name = $last_world_name;
		}
		//elseif ($non_world_world_count==1) { //assumes you want the one not called world (not a great assumption)
		//	$world_name = $non_world_world_name;
		//}
		else {
			$is_ready = false;
			if ($auto_choose_enable===true) {
				if ($non_world_world_name==null) {
					$world_name = $last_world_name;
				}
				else {
					$world_name = $non_world_world_name;
				}
			}
		}
	}
	if (isset($world_name)) {
		$chunkymapdata_thisworld_path = $chunkymapdata_worlds_path."/".$world_name;
	}
	return $is_ready;
}

?>


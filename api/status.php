<?php

if (!function_exists('str_contains')) {
    // monkey-patch PHP versions prior to 8:
    function str_contains($haystack, $needle) {
        return strpos($haystack, $needle) !== false;
    }
}

function append_at(&$meta, $key, $value, $spacer=" ") {
    if (!array_key_exists($key, $meta)) {
        $meta[$key] = $value;
    }
    else {
        $meta[$key] .= "$spacer" . $value;
    }
}

function push_at(&$meta, $key, $value) {
    if (!array_key_exists($key, $meta)) {
        $meta[$key] = array();
    }
    array_push($meta[$key], $value);
}

function get_server_meta() {
    $meta = array();
    // $p = popen("minebest list", "r");
    // pclose($p);
    // $cmd = "minebest list";
    // ^ needs work--says some are down when not down (tested on minetest.io)
    $cmd = "minetest-list";
    $out = shell_exec($cmd);

    // ^ returns nothing (only tested with minebest list) if triggered by public site visit
    //   so use ../mtanalyze/scripts/cron.hourly/update-server-status.sh
    //   for now.

    // echo "out=$out";
    if ($out === false) {
        $meta['error'] = "pipe cannot be established";
        return $meta;
    }
    elseif ($out === null) {
        $meta['error'] = "There was an error or no output for 'minebest list'.";
        return $meta;
    }
    $arr = preg_split('/\n/', $out);
    $line_n = 0;
    $count = 0;
    foreach ($arr as &$value) {
        $line = trim($value);
        $line_n += 1;  // Start counting at 1.
        if (strlen($line) < 1) {
            continue;
        }
        $parts = preg_split('/\s+/', $line);
        // ^ any whitespace or whitespace series is counted as one
        if (count($parts) == 4) {
            $server = array();
            $server['up'] = false;
            if ($parts[2] != "is") {
                append_at($server, 'error', '"is" should be the 3rd word but line $line_n is "$line".');
            }
            if ($parts[3] == "running") {
                $server['running'] = true;
            }
            $server['port'] = $parts[0];
            $server['name'] = $parts[1];
            push_at($meta, 'servers', $server);
            $count += 1;
        }
        else {
            if (!str_contains($line, "may be locked") and !str_contains($line, "Future versions")) {
                $error = "There was an unknown line from 'minebest list'.";
                $error .= " It should have 4 parts but had ".count($parts).": \"$line\".";
                append_at($meta, 'error', $error);
            }
        }
    }
    // echo "count=$count";
    // echo "servers" . $meta['servers'];
    return $meta;
}


$HOME = null;
if (array_key_exists('HOME', $_SERVER)) {
    // It's ok, it is not a Windows Server (that would be sad).
}
else {
    $HOME = $_SERVER['HOMEDRIVE'] . DIRECTORY_SEPARATOR .  $_SERVER['HOMEPATH'];
    preg_replace('#/+#', '/', $HOME);
}

// $CACHE = $HOME . DIRECTORY_SEPARATOR . ".cache" . DIRECTORY_SEPARATOR . "mtanalyze";
// $CACHE_JSON = $CACHE . DIRECTORY_SEPARATOR . "status.json";
$CACHE_JSON = dirname(__FILE__) . DIRECTORY_SEPARATOR . "status.json";
preg_replace('#/+#', '/', $CACHE_JSON);
$json_stat = false;

if (file_exists($CACHE_JSON)) {
    $json_stat = stat($CACHE_JSON);
}

$file_status = "do not refresh";

$refresh = false;
if ($json_stat === false) {
    $refresh = true;
    $file_status = "\"$CACHE_JSON\" not cached yet";
}
else {
    // $stat_msg = " ".json_encode(array('json_stat'=>$json_stat));
    // ^ checked and ok, so:
    $stat_msg = "";
    $json_mtime = $json_stat['mtime'];
    $time_sec = time();
    $age = $time_sec - $json_mtime;
    $max_age = 120;
    if ($age > $max_age) {
        $refresh = true;
        $file_status = "time $time_sec - cached JSON $json_mtime = $age: older than $max_age$stat_msg.";
    }
}

if ($refresh) {
    $meta = get_server_meta();
    $meta['file_status'] = $file_status;
    $jsonString = json_encode($meta);
    fwrite(STDERR, "* writing $CACHE_JSON at timestamp ".time()."...");
    $fp = fopen($CACHE_JSON, 'w');
    fwrite($fp, $jsonString);
    fclose($fp);
    fwrite(STDERR, "OK (wrote $CACHE_JSON)\n");
}
else {
    $jsonString = file_get_contents($CACHE_JSON);
    $refresh_msg = json_encode(array('refresh'=>$refresh));
    fwrite(STDERR, "* $refresh_msg loaded $CACHE_JSON\n");
    $meta = json_decode($jsonString, true);  // true for associative; false for object
    $meta['file_status'] = $file_status;
    if ($meta == null) {
        $meta = array();
        $meta['error'] = "$CACHE_JSON was not in JSON format: $jsonString";
        $meta['file_status'] = $file_status;
        $jsonString = json_encode($meta);
    }
}
echo "$jsonString\n";
?>

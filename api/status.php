<?php
$HOME = null;
if (array_key_exists('HOME', $_SERVER)) {
    // It's ok, it is not a Windows Server (that would be sad).
}
else {
    $HOME = $_SERVER['HOMEDRIVE'] . DIRECTORY_SEPARATOR .  $_SERVER['HOMEPATH'];
    preg_replace('#/+#', '/', $HOME);
}

$CACHE = $HOME . DIRECTORY_SEPARATOR . ".cache" . DIRECTORY_SEPARATOR . "mtanalyze";
$CACHE_JSON = $CACHE . DIRECTORY_SEPARATOR . "status.json";
preg_replace('#/+#', '/', $CACHE_JSON);
$json_stat = false;

if (file_exists($CACHE_JSON)) {
    $json_stat = stat($CACHE_JSON);
}

$refresh = false;
if ($json_stat === false) {
    $refresh = true;
}
else {
    $json_mtime = $json_stat['mtime'];
    $ago = time() - $json_mtime;
    if ($ago > 120) {
        $refresh = true;
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
    $out = shell_exec("minebest list");
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
            if ($parts[3] == "up") {
                $server['up'] = true;
            }
            $server['port'] = $parts[0];
            $server['name'] = $parts[1];
            push_at($meta, 'servers', $server);
            $count += 1;
        }
        else {
            $error = "There was an unknown line from 'minebest list'.";
            $error .= " It should have 4 parts but had ".count($parts).".";
            append_at($meta, 'error', $error);
        }
    }
    return $meta;
}

if ($refresh) {
    $meta = get_server_meta();
    $data = json_encode($meta);
    // TODO: save data
}
else {
    // TOOD: load data
    $data = "arst";
    $meta = json_decode($data);
}
echo $data;
?>

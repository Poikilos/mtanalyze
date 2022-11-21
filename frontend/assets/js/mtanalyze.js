// This script is from the https://github.com/poikilos/mtanalyze project
// by Jake Gustafson. The functions here require the API endpoint
// described in doc/web_API.md in the repo.

/**
 * Get a table row (tr) with a column count that always matches
 * header_col_count regardless of the length of the values array.
 * @param  {string[]} values - A list of literal values to add as content for each field
 * @param {int} header_col_count - The actual number of columns in the table where the result will go
 * @return {string} HTML defining a row (including start and end TR tags)
 */
const get_fixed_length_row = function(values, header_col_count, href) {
    var arrayLength = values.length
    var result = "<tr>"
    for (var i = 0; i < arrayLength; i++) {
        result += "<td"
        if (i == arrayLength - 1) {
            // Only make the last column span multiple cols.
            if (values.length < header_col_count) {
                result += ' colspan="' + (header_col_count-values.length) + '"'
            }
        }
        result += ">"
        if (href) {
            result += '<a href="' + href + '">'
        }
        result += values[i]
        if (href) {
            result += '</a>'
        }
        result += "</td>"
    }
    result += "</tr>"
    return result
}

/**
 * Write a row to a table describing the location and status of each
 * server (See update-server-status.sh for an example of how to generate
 * the required backend json file)
 * @param  {string} server_api_url - The URL of the mtanalyze API (server_api_url + "/status.json" must exist and match ../../doc/web_API.md)
 * @param  {string} tbody_id - The id of the tbody (The table must have a tbody since it will be cleared)
 * @param  {int} header_col_count - The actual number of columns in the table (Can be null or 0 to assume 4, but in that case, thead must be blank or 4 columns).
 */
const show_server_rows = async function(server_api_url, tbody_id, header_col_count, default_server_host) {
    if (!header_col_count) {
        header_col_count = 4
    }
    var tbody_el = document.getElementById(tbody_id)
    if (!tbody_el) {
        throw new Error("id does not exist: "+tbody_id);
    }
    tbody_el.innerHTML = get_fixed_length_row(["..."], header_col_count)
    // fetch uses promises. See <https://stackoverflow.com/a/54164027/4541104>
    const response = await fetch(server_api_url+'/status.json').then((response) => {
        if (response.status >= 400 && response.status < 600) {
            throw new Error("Bad response from server: "+response.status);
        }
        //const data = await response.json()
        // return response  // goes blank
        return response.json()
    }).then((returnedResponseJson) => {  // (returnedResponse)
        // Using response.json() here yields a blank object (JSON.stringify(returnedResponse) is "{}")
        const results = returnedResponseJson // returnedResponse.json()  // const results = JSON.parse(data)

        if (!results.servers) {
            // var obj_msg = ""
            // for (var prop in results) {
            //     if (Object.prototype.hasOwnProperty.call(obj, prop)) {
            //         obj_msg += " " + prop //+ "=" + obj[prop]
            //     }
            // }
            // ^ blank
            var obj_msg = JSON.stringify(results)
            throw new Error("Bad response from server: results.servers is "+results.servers+" (returnedResponse: "+obj_msg+")");
        }
        var arrayLength = results.servers.length
        document.getElementById(tbody_id).innerHTML = "";
        for (var i = 0; i < arrayLength; i++) {
            var status_msg = "down";
            if (results.servers[i].running) {
                status_msg = "running"
            }
            /*
            var row_data = "<tr><td>" + results.servers[i].name
            row_data += "</td><td>minetest.io"
            row_data += "</td><td>" + results.servers[i].port
            row_data += "</td><td>" + status_msg
            row_data += "</td></tr>"
            */
            var this_host = default_server_host;
            if (Object.prototype.hasOwnProperty.call(results.servers[i], 'host')) {
                if (results.servers[i].host) {
                    this_host = results.servers[i].host
                }
            }
            var url = '#' + results.servers[i].name;  // requires named anchors
            var fields = [
                results.servers[i].name,
                this_host,
                results.servers[i].port,
                status_msg,
            ]
            document.getElementById(tbody_id).innerHTML += get_fixed_length_row(fields, header_col_count, url)
        }
        // document.getElementById("server-status-loading-tr").innerHTML = "";
        // ^ not necessary (and no longer present by this point) since tbody gets erased.
    }).catch((error) => {
        var msg = ""+error;
        if (msg.includes("failed to fetch")) {
            msg += " " + server_api_url
            msg += ". Make sure the server is running and that this script is on the same machine (or that its CORS policy allows the host using this script)."
        }
        document.getElementById(tbody_id).innerHTML = get_fixed_length_row([msg], header_col_count)
    });
}

// See <https://devhints.io/jsdoc> for how to create JSDoc documentation
//   suitable for IDEs and documentation generators.

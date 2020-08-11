/*
 * Extract from the DOM the first and last IP addresses to be blocked,
 * and update the #network element with the CIDR representation of the
 * IP range which covers those.
 */
function updateBlockRange() {
    var ip_1 = $(":radio[name='ip-1']:checked")[0].value;
    var ip_2 = $(":radio[name='ip-2']:checked")[0].value;
    var range = computeBlockRange(ip_1, ip_2);
    $("#network").html(range.network + "/" + range.prefix_length);
}

/*
 * Given the first and last IP addresses (as "a.b.c.d" strings), to be
 * blocked, compute the smallest network and prefix length that will
 * cover them.
 */
function computeBlockRange(first_ip, last_ip) {
    var first = ipToBits(first_ip);
    var last = ipToBits(last_ip);
    var prefix = 0;
    var prefix_length = 0;
    var done = false;
    for (var i = 0; i < 32; i++) {
	prefix <<= 1;
	if (done) {
	    continue;
	}
	if (first[i] != last[i]) {
	    done = true;
	    continue;
	}
	prefix_length += 1;
	if (first[i] == '1') {
	    prefix |= 1;
	}
    }

    var o1 = (prefix & 0xff000000) >> 24;
    var o2 = (prefix & 0xff0000) >> 16;
    var o3 = (prefix & 0xff00) >> 8;
    var o4 = prefix & 0xff;

    network = o1 + "." + o2 + "." + o3 + "." + o4;
    return {'network':network, 'prefix_length':prefix_length};
}

/*
 * Given an IPv4 address (in "a.b.c.d" string format), return it as
 * an array of 32 integers, each representing a single bit.
 */
function ipToBits(ip_string) {
    var octets = ip_string.split(".").map(Number);
    var i = (octets[0] << 24) + (octets[1] << 16) + (octets[2] << 8) + octets[3];
    var zero_padded_bit_string = ("00000000000000000000000000000000" + i.toString(2)).slice(-32);
    return zero_padded_bit_string.split('');
}

$(document).ready(
    function() {
	// Check the first first-child and the last last-child radio buttons
	$("#ip-list > li:first-child > :radio[name='ip-1']").prop('checked', true);
	$("#ip-list > li:last-child > :radio[name='ip-2']").prop('checked', true);

	// Hook up event handler and force initial call
	$(".ip-radio").bind("change", updateBlockRange);
	updateBlockRange();
    });

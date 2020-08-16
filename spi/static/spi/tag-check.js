function checkTags() {
    const masterRegex = /{{sockmaster.*}}/;
    const puppetRegex = /{{sockpuppet.*}}/;

    $("span.cuEntry a.userlink[href*='/User:']").each(async function() {
	const wikitext = await getWikitext("User:" + this.text);
	let tagType = "";
	if (masterRegex.test(wikitext)) {
	    tagType = "M";
	} else if (puppetRegex.test(wikitext)) {
	    tagType = "P";
	}
	if (tagType != "") {
	    const status = tagStatus(wikitext);
	    $(this).before("<span style=\"background-color:"
			   + status.color
			   + "; border:darkgrey solid 1px; padding:1px;\" title=\""
			   + wikitext
			   + "\">"
			   + tagType
			   + " </span>");
	}
    });
};


async function getWikitext(pageTitle) {
    const api = new mw.Api();
    const request = {
	action: 'parse',
	page: pageTitle,
	prop: 'wikitext',
	formatversion: 2
    };
    try {
	const response = await api.get(request);
	if ('parse' in response) {
	    return response.parse.wikitext;
	}
    } catch (error) {
	return "";
    }
};


// Return an object with color: and tooltip: elements.
function tagStatus(wikitext) {
    const blockedRegex = /\|(2=)?blocked/;
    const provenRegex = /\|(2=)?proven/;
    const confirmedRegex = /\|(2=)?confirmed/;

    if (blockedRegex.test(wikitext)) {
	return {
	    color: "#ffff66",
	    tooltip: "blocked"
	};
    }
    if (provenRegex.test(wikitext)) {
	return {
	    color: "#ffcc99",
	    tooltip: "proven"
	};
    }
    if (confirmedRegex.test(wikitext)) {
	return {
	    color: "#ff3300",
	    tooltip: "confirmed"
	}
    }
    return {
	color: "#ffffff",
	tooltip: "unknown"
    };
}

// Cribbed from User:Writ Keeper/Scripts/cuStaleness.js
mw.hook('wikipage.content').add(function () {
    const titleRegex = /Wikipedia:Sockpuppet_investigations\/[^\/]+/;
    const sandboxRegex = /User:RoySmith\/sandbox/;
    //only use on a SPI page (or my sandbox for testing)
    const pageName = mw.config.get("wgPageName");
    if (titleRegex.test(pageName) || sandboxRegex.test(pageName)) {
	checkTags();
    }
});

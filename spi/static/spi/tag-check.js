//
// Main function.
//
function checkTags() {
    console.info("checkTags");
    $("span.cuEntry a.userlink[href*='/User:']").each(async function() {
	const wikitext = await getWikitext("User:" + this.text);
	const status = tagStatus(wikitext);
	if ('tagType' in status) {
	    $(this).before("<span style=\"background-color:"
			   + status.color
			   + "; border:darkgrey solid 1px; padding:1px;\" title=\""
			   + wikitext
			   + "\">"
			   + status.tagType
			   + " </span>");
	}
    });
};


//
// Given a page title (ex: "User:Foo"), return a Promise of a string
// containing the page's wikitext.
//
// On any kind of error, including the page not existing, the string
// is empty.
//
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

//
// Return an object describing how to style a SPI tag indicator.
//
// tagType: "M" for a sockmater, "P" for a sockpuppet
// color: what color to make the box.
// tooltip: a text description of the type of tag
//
// If there is no SPI tag, an empty object is returned.
//
function tagStatus(wikitext) {
    const masterRegex = /{{sockmaster.*}}/;
    const puppetRegex = /{{sockpuppet.*}}/;
    const blockedRegex = /\|(2=)?blocked/;
    const provenRegex = /\|(2=)?proven/;
    const confirmedRegex = /\|(2=)?confirmed/;

    let tagType = null;
    if (masterRegex.test(wikitext)) {
	tagType = "M";
    } else if (puppetRegex.test(wikitext)) {
	tagType = "P";
    }
    if (tagType == null) {
	return {};
    }

    if (blockedRegex.test(wikitext)) {
	return {
	    tagType: tagType,
	    color: "#ffff66",
	    tooltip: "blocked"
	};
    }
    if (provenRegex.test(wikitext)) {
	return {
	    tagType: tagType,
	    color: "#ffcc99",
	    tooltip: "proven"
	};
    }
    if (confirmedRegex.test(wikitext)) {
	return {
	    tagType: tagType,
	    color: "#ff3300",
	    tooltip: "confirmed"
	}
    }
    return {
	tagType: tagType,
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

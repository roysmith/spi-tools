//
// Main function.
//
async function checkTags(content) {
    content.find("span.cuEntry").each(async function() {
        const userNode = $(this).find("a[href*='/User:']")[0];
        const parseTree = await getParseTree("User:" + userNode.text);
        if (parseTree !== null) {
            const status = tagStatus(parseTree);
            if ('tagType' in status) {
                $(this).before("<span style=\"background-color:"
                               + status.color
                               + "; border:darkgrey solid 1px; padding:1px;\" title=\""
                               + status.tooltip
                               + "\">"
                               + status.tagType
                               + " </span>");
            }
        }
    });
};


//
// Given a page title (ex: "User:Foo"), return a Promise of a JSON
// parse tree.
//
// On any kind of error, null is returned.
//
async function getParseTree(pageTitle) {
    try {
        const page = await $.get('/api/rest_v1/page/html/' + pageTitle);
        const jsonText = findSpiTemplate(page);
        return JSON.parse(jsonText);
    } catch (error) {
        return null;
    }
};

//
// Given the parsoid text of a page, find the SPI-related template.
//
// Page is whatever a '/api/rest_v1/page/html/' API call returns.  The
// data-mw attribute for the template is returned as a JSON string.
//
// If the page contains multiple SPI templates, the first one is used.
//
function findSpiTemplate(page) {
    const $html = $($.parseHTML(page));
    const template = $html.find('[typeof="mw:Transclusion"]').filter(function() {
        try {
            const data = JSON.parse($(this).attr('data-mw'));
            return data["parts"][0]["template"]["target"]["wt"].match(/[sS]ock/);
        } catch(err) {
            return false;
        }
    });
    return template.attr('data-mw');
};


//
// Handle redirected template names.  This is playing whack-a-mole;
// it should really be handled on the server side.
//
function emulateRedirects(rawTemplateName) {
    switch(rawTemplateName) {
    case 'sockmaster':
        return 'sockpuppeteer';
    default:
        return rawTemplateName;
    }
}

//
// Return an object describing how to style a SPI tag indicator.
//
// tagType: "M" for a sockmater, "P" for a sockpuppet
// color: what color to make the box.
// tooltip: a text description of the type of tag
//
// If there is no SPI tag, an empty object is returned.
//
function tagStatus(parseTree) {
    const template = parseTree.parts[0].template;
    const rawTemplateName = template.target.wt.trim();
    const templateName = emulateRedirects(rawTemplateName).toLowerCase();
    let tagType = null;
    let typeParam = null;

    if (templateName == 'sockpuppeteer') {
        tagType = "M";
        const params = template.params;
        if ('1' in params) {
            typeParam = params[1].wt.trim();
        } else {
            typeParam = 'suspected';
        }
    } else if (templateName == 'sock' || templateName == 'sockpuppet') {
        tagType = "P";
        typeParam = template.params[2].wt.trim();
    } else if (templateName == 'checked sockpuppet') {
        tagType = "P";
        typeParam = 'confirmed';
    } else {
        return {};
    }

    if (typeParam == 'suspected') {
        return {
            tagType: tagType,
            color: "#ffffff",
            tooltip: "suspected"
        };
    }

    if (typeParam == 'blocked') {
        return {
            tagType: tagType,
            color: "#ffff66",
            tooltip: "blocked"
        };
    }
    if (typeParam == 'proven') {
        return {
            tagType: tagType,
            color: "#ffcc99",
            tooltip: "proven"
        };
    }
    if (typeParam == 'confirmed') {
        return {
            tagType: tagType,
            color: "#ff3300",
            tooltip: "confirmed"
        }
    }
    if (typeParam == 'banned') {
        return {
            tagType: tagType,
            color: "#7a00ff61",
            tooltip: "banned"
        }
    }
    return {
        tagType: tagType,
        color: "#ffffff",
        tooltip: "unknown"
    };
}

// There's probably a nicer way to do this.  The check for mw being undefined
// lets us import this file into QUnit for testing.
if (typeof mw !== "undefined") {
    // Cribbed from User:Writ Keeper/Scripts/cuStaleness.js
    mw.hook('wikipage.content').add(function (content) {
        const titleRegex = /Wikipedia:Sockpuppet_investigations\/[^\/]+/;
        const sandboxRegex = /User:RoySmith\/sandbox/;
        //only use on a SPI page (or my sandbox for testing)
        const pageName = mw.config.get("wgPageName");
        if (titleRegex.test(pageName) || sandboxRegex.test(pageName)) {
            checkTags(content);
        }
    });
};

//
// Main function.
//
async function checkTags() {
    $("span.cuEntry a[href*='/User:']").each(async function() {
        const parseTree = await getParseTree("User:" + this.text);
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
        const $html = $($.parseHTML(page));
        const jsonText = $html.find("table[typeof='mw:Transclusion'][data-mw*='sock']").attr('data-mw');
        return JSON.parse(jsonText);
    } catch (error) {
        return null;
    }
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
    const templateName = emulateRedirects(rawTemplateName);
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
    mw.hook('wikipage.content').add(function () {
        const titleRegex = /Wikipedia:Sockpuppet_investigations\/[^\/]+/;
        const sandboxRegex = /User:RoySmith\/sandbox/;
        //only use on a SPI page (or my sandbox for testing)
        const pageName = mw.config.get("wgPageName");
        if (titleRegex.test(pageName) || sandboxRegex.test(pageName)) {
            checkTags();
        }
    });
};

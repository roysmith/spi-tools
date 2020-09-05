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
    const templateName = template.target.wt;
    let tagType = null;
    let typeParam = null;

    if (templateName == 'sockmaster') {
        tagType = "M";
        typeParam = template.params[1].wt;
    } else if (templateName == 'sockpuppet') {
        tagType = "P";
        typeParam = template.params[2].wt;
    } else {
        return {};
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

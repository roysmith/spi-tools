'use strict';

/**
 * Fires on page load, adds the SPI-Tools portlet.
 *
 * pageTitle is the full title of the page this is running on,
 * i.e. "Wikipedia:Sockpuppet investigations/..."
 */
function spiTools_addLink(pageTitle) {
    mw.loader.using('mediawiki.util').then(function () {
        const parts = pageTitle.split('/');
        const last = parts.length - 1;
        const caseName = parts[last] == 'Archive' ? parts[last - 1] : parts[last];
        mw.util.addPortletLink('p-cactions',
                               'javascript:spiTools_init("' + caseName + '")',
                               'SPI Tools',
                               'ca-spiTools',
                               'Open SPI Tools');
    });
};

async function spiTools_init(caseName) {
    const baseURL = 'https://spi-tools.toolforge.org/spi/?caseName=';
    window.open(baseURL + caseName);
};

/**
 * Install on SPI pages
 */
mw.hook('wikipage.content').add(function () {
    const titleRegex = /Wikipedia:Sockpuppet_investigations\/[^\/]+/;
    const pageTitle = mw.config.get("wgPageName");
    if (titleRegex.test(pageTitle)) {
        spiTools_addLink(pageTitle);
    }
});

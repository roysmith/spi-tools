'use strict';

/**
 * Fires on page load, adds the SPI-Tools (dev) portlet.
 *
 * pageTitle is the full title of the page this is running on,
 * i.e. "Wikipedia:Sockpuppet investigations/..."
 */
function spiTools_dev_addLink(pageTitle) {
    mw.loader.using('mediawiki.util').then(function () {
        const parts = pageTitle.split('/');
        const last = parts.length - 1;
        const caseName = parts[last] == 'Archive' ? parts[last - 1] : parts[last];
        mw.util.addPortletLink('p-cactions',
                               'javascript:spiTools_dev_init("' + caseName + '")',
                               'SPI Tools (dev)',
                               'ca-spiTools-dev',
                               'Open SPI Tools (dev)');
    });
};

async function spiTools_dev_init(caseName) {
    const baseURL = 'https://spi-tools-dev.toolforge.org/spi/?caseName=';
    window.open(encodeURI(baseURL + caseName));
};

/**
 * Install on SPI pages
 */
mw.hook('wikipage.content').add(function () {
    const wikipediaNS = mw.config.get('wgNamespaceIds')['wikipedia']
    if (mw.config.get('wgNamespaceNumber') == wikipediaNS) {
        const titleRegex = /^Sockpuppet investigations\/[^\/]+/;
        const pageTitle = mw.config.get("wgTitle");
        if (titleRegex.test(pageTitle)) {
            spiTools_dev_addLink(pageTitle);
        }
    }
});

// Run by loading https://tools-static.wmflabs.org/spi-tools-dev/spi/tests.html

$.ajax({
    async: false,
    url: "tag-check.js",
    dataType: "script"
});

QUnit.module('tag-check', function() {
    QUnit.test('blocked puppet', function(assert) {
        // See test-data/User:Easternwikibot@855814186.parsoid.html
        const rawDataMw = '{"parts":[{"template":{"target":{"wt":"sockpuppet","href":"./Template:Sockpuppet"},"params":{"1":{"wt":"Jimchu23"},"2":{"wt":"blocked"}},"i":0}}]}';
        const parseTree = JSON.parse(rawDataMw);
        const status = tagStatus(parseTree);
        const expectedStatus = {tagType: "P",
                                color: "#ffff66",
                                tooltip: "blocked"
                               };
        assert.propEqual(status, expectedStatus);
    });

    QUnit.test('bare sockmaster (#118)', function(assert) {
        // See test-data/User:Mopterhlaf@982661804.parsoid.html
        const rawDataMw = '{"parts":[{"template":{"target":{"wt":"sockmaster","href":"./Template:Sockmaster"},"params":{},"i":0}}]}';
        const parseTree = JSON.parse(rawDataMw);
        const status = tagStatus(parseTree);
        const expectedStatus = {tagType: "M",
                                color: "#ffffff",
                                tooltip: "suspected"
                               };
        assert.propEqual(status, expectedStatus);
    });

    QUnit.test('checked sockpuppet (#119)', function(assert) {
        const rawDataMw ='{"parts":[{"template":{"target":{"wt":"Checked sockpuppet","href":"./Template:Checked_sockpuppet"},"params":{"1":{"wt":"Prince Shobuz"}},"i":0}}]}';
        const parseTree = JSON.parse(rawDataMw);
        const status = tagStatus(parseTree);
        const expectedStatus = {tagType: "P",
                                color: "#ff3300",
                                tooltip: "confirmed"
                               };
        assert.propEqual(status, expectedStatus);
    });

    QUnit.test('sockpuppet proven', function(assert) {
        const rawDataMw = '{"parts":[{"template":{"target":{"wt":"Sockpuppet","href":"./Template:Sockpuppet"},"params":{"1":{"wt":"JesusLuna19"},"2":{"wt":"proven"}},"i":0}}]}';
        const parseTree = JSON.parse(rawDataMw);
        const status = tagStatus(parseTree);
        const expectedStatus = {tagType: "P",
                                color: "#ffcc99",
                                tooltip: "proven"
                               };
        assert.propEqual(status, expectedStatus);
    });

    async function getParsoidText(pageTitle) {
        const url = 'https://en.wikipedia.org//api/rest_v1/page/html/' + pageTitle;
        return $.get(url);
    };

    QUnit.test('select uppercase template name (#109)', async function(assert) {
        // It's not clear why the <section> wrapper is needed here.  This is partly explained by
        // https://stackoverflow.com/questions/15403600/jquery-not-finding-elements-in-jquery-parsehtml-result
        // but not entirely.  You can, for example, replace <section> with <div> or <span> and it still
        // works, but replacing it with <p> will fail.
        let parsoidText = `<section><table typeof="mw:Transclusion" data-mw='{"parts":[{"template":{"target":{"wt":"Sockpuppet","href":"./Template:Sockpuppet"},"params":{"1":{"wt":"JesusLuna19"},"2":{"wt":"proven"}},"i":0}}]}'></table></section>`;
        const template = findSpiTemplate(parsoidText);
        assert.ok(template);
    });
});

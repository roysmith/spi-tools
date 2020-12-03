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
});

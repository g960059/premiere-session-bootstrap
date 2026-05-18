(function () {
  function selectedProjectItems() {
    try {
      if (app.project && app.project.getSelection) {
        return app.project.getSelection();
      }
    } catch (error) {
      return {error: String(error)};
    }
    return [];
  }

  var selection = selectedProjectItems();
  var report = {
    generatedAt: new Date().toISOString(),
    selectionCount: selection && selection.length ? selection.length : 0,
    items: []
  };

  if (selection && selection.length) {
    for (var i = 0; i < selection.length; i++) {
      var item = selection[i];
      report.items.push({
        name: item.name,
        type: item.type,
        mediaPath: item.getMediaPath ? item.getMediaPath() : null,
        keys: (function () {
          var keys = [];
          for (var key in item) {
            keys.push(key);
          }
          keys.sort();
          return keys;
        })()
      });
    }
  }

  var path = "/tmp/premiere-bootstrap-selection-probe.json";
  var out = new File(path);
  out.encoding = "UTF-8";
  out.open("w");
  out.write(JSON.stringify(report, null, 2));
  out.close();

  return "PASS: wrote " + path + " with " + report.selectionCount + " selected item(s)";
})();


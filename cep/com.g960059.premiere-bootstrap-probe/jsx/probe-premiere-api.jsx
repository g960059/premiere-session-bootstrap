(function () {
  function probe(path, owner, name) {
    var value = owner ? owner[name] : undefined;
    return {
      path: path,
      type: typeof value,
      exists: typeof value !== "undefined" && value !== null
    };
  }

  function ownKeys(object) {
    var keys = [];
    try {
      for (var key in object) {
        keys.push(key);
      }
    } catch (error) {
      keys.push("ERROR:" + String(error));
    }
    keys.sort();
    return keys;
  }

  var report = {
    generatedAt: new Date().toISOString(),
    appName: app ? app.name : null,
    appVersion: app ? app.version : null,
    build: app ? app.build : null,
    projectName: app && app.project ? app.project.name : null,
    probes: [],
    projectKeys: app && app.project ? ownKeys(app.project) : [],
    rootItemKeys: app && app.project && app.project.rootItem ? ownKeys(app.project.rootItem) : [],
    qe: {
      beforeEnable: typeof qe !== "undefined",
      afterEnable: null,
      keys: []
    },
    multicamSearch: []
  };

  report.probes.push(probe("app.project.importFiles", app.project, "importFiles"));
  report.probes.push(probe("app.project.rootItem.createBin", app.project.rootItem, "createBin"));
  report.probes.push(probe("app.project.createNewSequence", app.project, "createNewSequence"));
  report.probes.push(probe("app.project.createNewSequenceFromClips", app.project, "createNewSequenceFromClips"));
  report.probes.push(probe("app.project.openSequence", app.project, "openSequence"));
  report.probes.push(probe("app.project.save", app.project, "save"));
  report.probes.push(probe("app.enableQE", app, "enableQE"));

  try {
    if (app.enableQE) {
      app.enableQE();
    }
    report.qe.afterEnable = typeof qe !== "undefined";
    if (typeof qe !== "undefined") {
      report.qe.keys = ownKeys(qe);
    }
  } catch (qeError) {
    report.qe.error = String(qeError);
  }

  var searchTerms = ["multi", "sync", "sequence", "audio", "clip"];
  var containers = [
    {name: "app.project", object: app.project},
    {name: "app.project.rootItem", object: app.project.rootItem},
    {name: "qe", object: typeof qe !== "undefined" ? qe : null},
    {name: "qe.project", object: typeof qe !== "undefined" ? qe.project : null}
  ];
  for (var c = 0; c < containers.length; c++) {
    var container = containers[c];
    var keys = ownKeys(container.object);
    for (var k = 0; k < keys.length; k++) {
      var lower = String(keys[k]).toLowerCase();
      for (var s = 0; s < searchTerms.length; s++) {
        if (lower.indexOf(searchTerms[s]) >= 0) {
          report.multicamSearch.push(container.name + "." + keys[k]);
          break;
        }
      }
    }
  }

  var path = "/tmp/premiere-bootstrap-api-probe.json";
  var out = new File(path);
  out.encoding = "UTF-8";
  out.open("w");
  out.write(JSON.stringify(report, null, 2));
  out.close();

  return "PASS: wrote " + path;
})();


/*
Premiere Pro ExtendScript API probe.

Run inside Premiere Pro's ExtendScript environment. It writes a JSON-ish report
to ~/Desktop/premiere-api-probe.json.
*/

(function () {
    function exists(path, value) {
        return {
            path: path,
            type: typeof value,
            exists: typeof value !== "undefined" && value !== null
        };
    }

    function method(path, owner, name) {
        var value = owner ? owner[name] : undefined;
        return exists(path, value);
    }

    var report = {
        appName: app ? app.name : null,
        appVersion: app ? app.version : null,
        probes: []
    };

    report.probes.push(method("app.project.importFiles", app.project, "importFiles"));
    report.probes.push(method("app.project.rootItem.createBin", app.project.rootItem, "createBin"));
    report.probes.push(method("app.project.createNewSequence", app.project, "createNewSequence"));
    report.probes.push(method("app.project.createNewSequenceFromClips", app.project, "createNewSequenceFromClips"));
    report.probes.push(method("app.project.openSequence", app.project, "openSequence"));
    report.probes.push(method("app.project.save", app.project, "save"));
    report.probes.push(method("app.enableQE", app, "enableQE"));
    report.probes.push(exists("qe", typeof qe !== "undefined" ? qe : undefined));

    // There may not be a public direct API for multicam source sequence creation.
    // Keep these string probes in the report so manual review can confirm whether
    // a given Premiere version exposes anything relevant.
    report.multicam_search_terms = [
        "createMultiCam",
        "createMulticam",
        "multiCamera",
        "multicam",
        "synchronize"
    ];

    var out = new File(Folder.desktop.fsName + "/premiere-api-probe.json");
    out.encoding = "UTF-8";
    out.open("w");
    out.write(JSON.stringify(report, null, 2));
    out.close();
    alert("Premiere API probe written to " + out.fsName);
})();


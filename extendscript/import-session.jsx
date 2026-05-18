/*
Conservative Premiere import prototype.

Edit MANIFEST_PATH, then run inside Premiere Pro. This script creates take bins
and imports the files listed in premiere-manifest.json. It intentionally does
not create multicam sequences yet.
*/

var MANIFEST_PATH = "/ABSOLUTE/PATH/TO/reports/premiere-manifest.json";

(function () {
    function readJson(path) {
        var file = new File(path);
        if (!file.exists) {
            throw new Error("Manifest not found: " + path);
        }
        file.encoding = "UTF-8";
        file.open("r");
        var text = file.read();
        file.close();
        return JSON.parse(text);
    }

    function findChildBin(parent, name) {
        for (var i = 0; i < parent.children.numItems; i++) {
            var item = parent.children[i];
            if (item && item.name === name && item.type === ProjectItemType.BIN) {
                return item;
            }
        }
        return null;
    }

    function ensureBinPath(root, names) {
        var current = root;
        for (var i = 0; i < names.length; i++) {
            var next = findChildBin(current, names[i]);
            if (!next) {
                next = current.createBin(names[i]);
            }
            current = next;
        }
        return current;
    }

    function importIntoBin(paths, bin) {
        if (!paths.length) {
            return;
        }
        app.project.importFiles(paths, true, bin, false);
    }

    var manifest = readJson(MANIFEST_PATH);
    var root = app.project.rootItem;
    var imported = 0;

    for (var t = 0; t < manifest.takes.length; t++) {
        var take = manifest.takes[t];
        var bin = ensureBinPath(root, take.bin_path);
        var paths = [];
        for (var c = 0; c < take.camera_files.length; c++) {
            paths.push(take.camera_files[c].path);
        }
        paths.push(take.edit_audio.path);
        importIntoBin(paths, bin);
        imported += paths.length;
    }

    alert("Imported " + imported + " file(s) from Premiere manifest.");
})();


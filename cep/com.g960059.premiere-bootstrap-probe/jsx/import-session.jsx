/*
Premiere import/bootstrap runner.

Run inside Premiere Pro. If MANIFEST_PATH is left empty, the script opens a
file picker for reports/premiere-manifest.json.

This creates/opens the project named in the manifest, creates take bins,
imports angle videos plus the final external audio, saves the project, and
writes reports/premiere-import-result.json.

It intentionally does not create audio-synced multicam source sequences.
*/

var MANIFEST_PATH = "";

(function () {
    function chooseManifestPath() {
        if (MANIFEST_PATH && MANIFEST_PATH.length) {
            return MANIFEST_PATH;
        }
        var file = File.openDialog("Select premiere-manifest.json", "*.json");
        if (!file) {
            throw new Error("No manifest selected.");
        }
        return file.fsName;
    }

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

    function writeJson(path, payload) {
        var file = new File(path);
        file.encoding = "UTF-8";
        file.open("w");
        file.write(JSON.stringify(payload, null, 2));
        file.close();
    }

    function dirname(path) {
        var index = Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\"));
        return index >= 0 ? path.substring(0, index) : "";
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
                if (!next) {
                    throw new Error("Failed to create bin: " + names.slice(0, i + 1).join("/"));
                }
            }
            current = next;
        }
        return current;
    }

    function mediaAlreadyInBin(bin, path) {
        for (var i = 0; i < bin.children.numItems; i++) {
            var item = bin.children[i];
            if (!item || item.type === ProjectItemType.BIN) {
                continue;
            }
            if (item.getMediaPath && item.getMediaPath() === path) {
                return true;
            }
        }
        return false;
    }

    function ensureProject(projectPath) {
        if (!projectPath) {
            return "used_current_project";
        }
        if (app.project && app.project.path === projectPath) {
            return "project_already_open";
        }
        var projectFile = new File(projectPath);
        if (projectFile.exists) {
            if (!app.openDocument(projectPath, true, true, true, true)) {
                throw new Error("Failed to open project: " + projectPath);
            }
            return "opened_existing_project";
        }
        var projectFolder = new Folder(dirname(projectPath));
        if (!projectFolder.exists) {
            projectFolder.create();
        }
        if (!app.newProject(projectPath)) {
            throw new Error("Failed to create project: " + projectPath);
        }
        return "created_new_project";
    }

    function importMissing(paths, bin) {
        var missing = [];
        for (var i = 0; i < paths.length; i++) {
            var path = paths[i];
            if (!new File(path).exists) {
                throw new Error("Media file not found: " + path);
            }
            if (!mediaAlreadyInBin(bin, path)) {
                missing.push(path);
            }
        }
        if (missing.length) {
            if (!app.project.importFiles(missing, true, bin, false)) {
                throw new Error("Premiere importFiles failed for bin: " + bin.name);
            }
        }
        return missing.length;
    }

    var manifestPath = chooseManifestPath();
    var manifest = readJson(manifestPath);
    var report = {
        schema: "premiere-session-bootstrap.import-result.v1",
        manifest_path: manifestPath,
        project_path: manifest.premiere_project_path,
        project_action: null,
        take_count: manifest.takes.length,
        imported_file_count: 0,
        skipped_existing_count: 0,
        takes: []
    };

    report.project_action = ensureProject(manifest.premiere_project_path);
    var root = app.project.rootItem;

    for (var t = 0; t < manifest.takes.length; t++) {
        var take = manifest.takes[t];
        var bin = ensureBinPath(root, take.bin_path);
        var paths = [];
        for (var c = 0; c < take.camera_files.length; c++) {
            paths.push(take.camera_files[c].path);
        }
        paths.push(take.edit_audio.path);
        var imported = importMissing(paths, bin);
        report.imported_file_count += imported;
        report.skipped_existing_count += paths.length - imported;
        report.takes.push({
            take_id: take.take_id,
            bin_path: take.bin_path.join("/"),
            multicam_name: take.multicam_name,
            file_count: paths.length,
            imported_file_count: imported,
            skipped_existing_count: paths.length - imported,
            final_audio: take.edit_audio.file,
            next_manual_step: "Select the imported take media, then create a multicam source sequence using Audio sync."
        });
    }

    app.project.save();
    writeJson(dirname(manifestPath) + "/premiere-import-result.json", report);
    alert("Premiere bootstrap complete. Imported " + report.imported_file_count + " new file(s); skipped " + report.skipped_existing_count + " existing file(s).");
})();

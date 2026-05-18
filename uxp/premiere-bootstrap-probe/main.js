async function runProbe() {
  const out = document.getElementById("out");
  const report = {
    generatedAt: new Date().toISOString(),
    hasRequire: typeof require === "function",
    premierepro: null,
    uxp: null,
    error: null
  };

  try {
    const ppro = require("premierepro");
    const app = ppro.Application || ppro.app || null;
    const project = ppro.Project || null;
    const sequence = ppro.Sequence || null;
    const sequenceEditor = ppro.SequenceEditor || null;
    report.premierepro = {
      topLevelKeys: Object.keys(ppro || {}).sort(),
      appKeys: Object.keys(app || {}).sort(),
      projectStaticKeys: Object.keys(project || {}).sort(),
      sequenceStaticKeys: Object.keys(sequence || {}).sort(),
      sequenceEditorStaticKeys: Object.keys(sequenceEditor || {}).sort(),
      hasCreateProject: Boolean(project && project.createProject),
      hasOpenProject: Boolean(project && project.open),
      hasCreateSequenceFromMedia: false,
      hasMulticamNamedApi: Object.keys(ppro || {}).some((key) => /multi|sync/i.test(key))
    };

    if (project && project.getActiveProject) {
      const activeProject = await project.getActiveProject();
      report.premierepro.activeProjectKeys = Object.keys(activeProject || {}).sort();
      report.premierepro.activeProjectName = activeProject && activeProject.name;
      report.premierepro.hasCreateSequenceFromMedia = Boolean(
        activeProject && activeProject.createSequenceFromMedia
      );
    }
  } catch (error) {
    report.error = String(error && error.stack ? error.stack : error);
  }

  try {
    const uxp = require("uxp");
    report.uxp = {
      keys: Object.keys(uxp || {}).sort(),
      storageKeys: uxp.storage ? Object.keys(uxp.storage).sort() : [],
      versions: uxp.versions || null
    };
  } catch (error) {
    report.uxp = { error: String(error && error.stack ? error.stack : error) };
  }

  out.textContent = JSON.stringify(report, null, 2);
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("run").addEventListener("click", runProbe);
});

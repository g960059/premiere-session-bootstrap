(function () {
  const out = document.getElementById("out");

  function evalScript(source) {
    return new Promise((resolve) => {
      window.__adobe_cep__.evalScript(source, (result) => resolve(result));
    });
  }

  async function runFile(relativePath) {
    const extensionRoot = window.__adobe_cep__.getSystemPath("extension").replace(/\\/g, "/");
    const scriptPath = `${extensionRoot}/${relativePath}`;
    out.textContent = `Running ${scriptPath} ...`;
    const result = await evalScript(`$.evalFile("${scriptPath}")`);
    out.textContent = String(result);
  }

  document.getElementById("runProbe").addEventListener("click", () => {
    runFile("jsx/probe-premiere-api.jsx");
  });

  document.getElementById("runSelectionProbe").addEventListener("click", () => {
    runFile("jsx/probe-selection.jsx");
  });
})();


const cp = require("child_process");

const { compareVersions } = require("compare-versions");
const which = require("which");

const EXEC_OPTIONS = { encoding: "utf8", stdio: [0, null, null] };

function isProgramInstalled(program) {
  return new Boolean(which.sync(program, { nothrow: true }));
}

function getPythonVersionFromExecutable(executable) {
  const pythonPath = which.sync(executable, { nothrow: true });
  const child = cp.execSync(`${pythonPath} -V`, EXEC_OPTIONS);
  const out = Buffer.from(child).toString("ascii");
  if (!out || !out.includes(" ")) {
    return "0.0.0";
  }
  return out.split(" ")[1].replace("\n", "");
}

function main() {
  // Check if Python is installed
  const isPythonInstalled = isProgramInstalled("python");
  if (!isPythonInstalled) {
    console.error("Python must be installed before install project-config.");
    return 1;
  }

  // Check the minimum version of Python
  let pythonExecutable = "python";
  let pythonVersion = getPythonVersionFromExecutable(pythonExecutable);

  if (compareVersions(pythonVersion, "3") < 0) {
    pythonExecutable = "python3";
    pythonVersion = getPythonVersionFromExecutable(pythonExecutable);
  }

  if (compareVersions(pythonVersion, "3.7") < 0) {
    console.error(
      "The Python version must be >= 3.7 to install project-config"
    );
    return 1;
  }

  // Install project-config
  process.stdout.write("Installing project-config...");
  cp.execSync(
    `${pythonExecutable} -mpip install -U project-config`,
    EXEC_OPTIONS
  );
  console.log(" OK");
  return 0;
}

process.exit(main());

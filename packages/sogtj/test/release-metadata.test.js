const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const scriptPath = path.join(__dirname, "..", "bin", "sogtj.js");
const scriptText = fs.readFileSync(scriptPath, "utf8");

test("release metadata matches the published 0.1.7 installer on R2", () => {
  const packageVersion = scriptText.match(/const PACKAGE_VERSION = "([^"]+)";/);
  const installerVersion = scriptText.match(/const INSTALLER_VERSION = "([^"]+)";/);
  const sha256 = scriptText.match(/const DEFAULT_SHA256 = "([0-9a-f]+)";/);

  assert.ok(packageVersion, "PACKAGE_VERSION should be present");
  assert.ok(installerVersion, "INSTALLER_VERSION should be present");
  assert.ok(sha256, "DEFAULT_SHA256 should be present");
  assert.equal(packageVersion[1], "0.1.11");
  assert.equal(installerVersion[1], "0.1.7");
  assert.equal(
    sha256[1],
    "7dcf3e47f5b298c4155196262df140709701042aaed3fbc0725e0c99d052878f",
  );
});

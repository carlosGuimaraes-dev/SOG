#!/usr/bin/env node

const childProcess = require("node:child_process");
const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const https = require("node:https");
const os = require("node:os");
const path = require("node:path");
const { pipeline } = require("node:stream/promises");

const PACKAGE_VERSION = "0.1.11";
const INSTALLER_VERSION = "0.1.7";
const DISPLAY_NAME = "iSOG";
const DOWNLOAD_BASE = "https://sog.carlosguimaraes.us/sogtj";
const DEFAULT_ASSET_NAME = `SOG.Desktop.Setup.${INSTALLER_VERSION}.exe`;
const DEFAULT_SHA256 = "7dcf3e47f5b298c4155196262df140709701042aaed3fbc0725e0c99d052878f";

function usage() {
  console.log(`
${DISPLAY_NAME} installer

Uso:
  npx -y sogtj

Opcoes:
  --help          Mostra esta ajuda.
  --dry-run       Mostra o instalador que seria baixado/executado.
  --verify-only   Baixa e valida o instalador, mas nao executa.

Variaveis:
  ISOG_VERSION     Versao do instalador. Padrao: ${INSTALLER_VERSION}
  ISOG_ASSET_URL   URL direta do instalador Windows.
  ISOG_ASSET_NAME  Nome do asset na release. Padrao: ${DEFAULT_ASSET_NAME}
`);
}

function parseArgs(argv) {
  const flags = new Set(argv);
  return {
    help: flags.has("--help") || flags.has("-h"),
    dryRun: flags.has("--dry-run"),
    verifyOnly: flags.has("--verify-only"),
  };
}

function requireWindows() {
  if (process.platform !== "win32") {
    throw new Error(`${DISPLAY_NAME} ${INSTALLER_VERSION} ainda esta disponivel apenas para Windows.`);
  }
}

function getInstallConfig() {
  const version = process.env.ISOG_VERSION || INSTALLER_VERSION;
  const assetName = process.env.ISOG_ASSET_NAME || `SOG.Desktop.Setup.${version}.exe`;
  const assetUrl = process.env.ISOG_ASSET_URL || `${DOWNLOAD_BASE}/v${version}/${encodeURIComponent(assetName)}`;
  const cacheRoot = process.env.LOCALAPPDATA || os.tmpdir();
  const cacheDir = path.join(cacheRoot, "iSOG", "installers", version);

  return {
    version,
    assetName,
    assetUrl,
    expectedSha256: process.env.ISOG_SHA256 || DEFAULT_SHA256,
    cacheDir,
    installerPath: path.join(cacheDir, assetName),
  };
}

async function ensureDir(dir) {
  await fs.promises.mkdir(dir, { recursive: true });
}

async function fileExists(filePath) {
  try {
    await fs.promises.access(filePath, fs.constants.R_OK);
    return true;
  } catch (_) {
    return false;
  }
}

async function sha256(filePath) {
  const hash = crypto.createHash("sha256");
  const input = fs.createReadStream(filePath);

  await new Promise((resolve, reject) => {
    input.on("data", (chunk) => hash.update(chunk));
    input.on("error", reject);
    input.on("end", resolve);
  });

  return hash.digest("hex");
}

function request(url, redirectsLeft = 5) {
  const client = url.startsWith("https:") ? https : http;

  return new Promise((resolve, reject) => {
    const req = client.get(url, (res) => {
      const statusCode = res.statusCode || 0;
      const location = res.headers.location;

      if ([301, 302, 303, 307, 308].includes(statusCode) && location && redirectsLeft > 0) {
        res.resume();
        resolve(request(new URL(location, url).toString(), redirectsLeft - 1));
        return;
      }

      if (statusCode < 200 || statusCode >= 300) {
        res.resume();
        reject(new Error(`Download falhou com HTTP ${statusCode}: ${url}`));
        return;
      }

      resolve(res);
    });

    req.on("error", reject);
  });
}

async function download(url, destination) {
  const partial = `${destination}.download`;
  const res = await request(url);
  await pipeline(res, fs.createWriteStream(partial));
  await fs.promises.rename(partial, destination);
}

async function ensureInstaller(config) {
  await ensureDir(config.cacheDir);

  if (!(await fileExists(config.installerPath))) {
    console.log(`Baixando ${DISPLAY_NAME} ${config.version}...`);
    await download(config.assetUrl, config.installerPath);
  }

  if (config.expectedSha256) {
    const actual = await sha256(config.installerPath);
    if (actual.toLowerCase() !== config.expectedSha256.toLowerCase()) {
      await fs.promises.rm(config.installerPath, { force: true });
      throw new Error('O instalador baixado nao passou na verificacao de integridade. Tente executar o comando novamente.');
    }
  }
}

function runInstaller(installerPath) {
  console.log(`Abrindo instalador: ${installerPath}`);
  const child = childProcess.spawn(installerPath, [], {
    detached: true,
    stdio: "ignore",
    windowsHide: false,
  });

  child.unref();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    usage();
    return;
  }

  const config = getInstallConfig();

  if (args.dryRun) {
    const { expectedSha256, ...publicConfig } = config;
    console.log(JSON.stringify({ ...publicConfig, integrityCheck: 'enabled' }, null, 2));
    return;
  }

  requireWindows();

  await ensureInstaller(config);

  if (args.verifyOnly) {
    console.log(`${DISPLAY_NAME} ${config.version} baixado e validado em ${config.installerPath}`);
    return;
  }

  runInstaller(config.installerPath);
}

main().catch((error) => {
  console.error(`Erro: ${error.message}`);
  process.exit(1);
});

import {rename, access} from "node:fs/promises";
import {constants} from "node:fs";
import {spawn} from "node:child_process";
import path from "node:path";
import process from "node:process";

const projectRoot = process.cwd();
const apiDir = path.join(projectRoot, "src", "app", "api");
const disabledApiDir = path.join(projectRoot, "src", "app", "__desktop_api_disabled__");

async function pathExists(targetPath) {
  try {
    await access(targetPath, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function runNextBuild() {
  return new Promise((resolve, reject) => {
    const child = spawn(
      process.platform === "win32" ? "npx.cmd" : "npx",
      ["next", "build"],
      {
        cwd: projectRoot,
        stdio: "inherit",
        env: {
          ...process.env,
          DESKTOP_BUILD: "true",
          NEXT_PUBLIC_IM_TRANSPORT: "direct"
        }
      }
    );

    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }

      reject(new Error(`Desktop Next build failed with exit code ${code ?? -1}.`));
    });

    child.on("error", reject);
  });
}

async function main() {
  const hasApiDir = await pathExists(apiDir);
  const hasDisabledApiDir = await pathExists(disabledApiDir);

  if (hasDisabledApiDir) {
    throw new Error("Found existing desktop-disabled api directory. Please restore frontend/src/app/api before continuing.");
  }

  try {
    if (hasApiDir) {
      await rename(apiDir, disabledApiDir);
    }

    await runNextBuild();
  } finally {
    const disabledStillExists = await pathExists(disabledApiDir);
    const apiStillExists = await pathExists(apiDir);

    if (disabledStillExists && !apiStillExists) {
      await rename(disabledApiDir, apiDir);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

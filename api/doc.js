const fs = require("fs");
const path = require("path");

function loadManifest() {
  const manifestPath = path.join(__dirname, "..", "public", "book-manifest.json");
  return JSON.parse(fs.readFileSync(manifestPath, "utf8"));
}

function safeResolveUnderRoot(root, rel) {
  const full = path.resolve(root, rel);
  const rootWithSep = root.endsWith(path.sep) ? root : root + path.sep;
  if (full !== root && !full.startsWith(rootWithSep)) {
    return null;
  }
  return full;
}

module.exports = (req, res) => {
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  if (req.method !== "GET") {
    res.status(405).json({ error: "method not allowed" });
    return;
  }

  let manifest;
  try {
    manifest = loadManifest();
  } catch (e) {
    res.status(500).json({ error: "manifest_missing", detail: String(e && e.message ? e.message : e) });
    return;
  }

  const key = String(req.query.key || "");
  const rel = manifest.keys && manifest.keys[key];
  if (!rel || typeof rel !== "string") {
    res.status(400).json({ error: "unknown_key" });
    return;
  }

  const root = process.cwd();
  const full = safeResolveUnderRoot(root, rel);
  if (!full) {
    res.status(400).json({ error: "bad_path" });
    return;
  }

  if (!fs.existsSync(full) || !fs.statSync(full).isFile()) {
    res.status(404).json({ error: "not_found", path: rel });
    return;
  }

  const markdown = fs.readFileSync(full, "utf8");
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.status(200).send(JSON.stringify({ key, path: rel, markdown }));
};

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const draft = process.argv.includes("--draft");
const evidencePath = path.join(root, "poster", "evidence.json");
const metricsPath = path.join(root, "evidence", "performance-aws.json");
const evidence = await fs.readFile(evidencePath, "utf8").then(JSON.parse).catch(() => ({}));
const metrics = await fs.readFile(metricsPath, "utf8").then(JSON.parse).catch(() => null);
const localMetrics = await fs.readFile(path.join(root, "evidence", "performance-local.json"), "utf8")
  .then(JSON.parse).catch(() => null);
if (!draft && (!evidence.aws_verified || !evidence.roles || !metrics)) {
  throw new Error("Final slides need verified AWS evidence, team roles, and AWS metrics");
}

const C = {
  navy: "#13283f", blue: "#216d92", teal: "#247aa0", pale: "#eaf3f8",
  paper: "#f7fafc", line: "#c5d7e2", muted: "#486075", white: "#ffffff",
  light: "#dff0f5", gray: "#e9eff3",
};
const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function shape(slide, geometry, x, y, w, h, fill = C.white, stroke = "none") {
  return slide.shapes.add({
    geometry, position: { left: x, top: y, width: w, height: h }, fill,
    line: { style: "solid", fill: stroke, width: stroke === "none" ? 0 : 2 },
  });
}
function txt(slide, value, x, y, w, h, size = 22, color = C.navy, bold = false) {
  const box = shape(slide, "textbox", x, y, w, h, "none");
  box.text = value;
  box.text.style = { fontFamily: "Arial", fontSize: size, bold, color };
  return box;
}
function card(slide, x, y, w, h, title, body, fill = C.white) {
  shape(slide, "roundRect", x, y, w, h, fill, C.line);
  txt(slide, title, x + 25, y + 20, w - 50, 42, 25, C.navy, true);
  txt(slide, body, x + 25, y + 73, w - 50, h - 90, 21, C.muted);
}
function base(title, kicker = "JOBTRACK · GROUP 42") {
  const slide = deck.slides.add();
  slide.background.fill = C.paper;
  shape(slide, "rect", 0, 0, 1280, 18, C.blue);
  txt(slide, kicker, 70, 38, 1060, 28, 15, C.teal, true);
  txt(slide, title, 70, 84, 1130, 70, 42, C.navy, true);
  return slide;
}
async function addImage(slide, imagePath, x, y, w, h, alt) {
  const bytes = await fs.readFile(imagePath);
  slide.images.add({
    blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    contentType: "image/png", alt, fit: "contain",
    position: { left: x, top: y, width: w, height: h },
  });
}
function note(slide, text) { slide.speakerNotes.text = text; }

// 1 · Cover
{
  const slide = deck.slides.add();
  slide.background.fill = C.navy;
  shape(slide, "rect", 0, 0, 24, 720, C.teal);
  txt(slide, "JobTrack", 78, 125, 630, 120, 78, C.white, true);
  txt(slide, evidence.aws_verified ? "A private cloud-hosted job application tracker" :
      "A private job application tracker · AWS deployment planned", 82, 259, 590, 120, 33, C.white);
  txt(slide, "CSE 4333 Cloud Computing · Group 42", 82, 515, 800, 36, 23, C.white, true);
  txt(slide, "Ahmad Salem · afs1009@mavs.uta.edu\nNoorAldeen Waleed · nxw3312@mavs.uta.edu", 82, 564, 930, 95, 20, C.white);
  shape(slide, "roundRect", 795, 156, 328, 76, C.pale);
  txt(slide, "Capture a job", 825, 175, 270, 40, 25, C.navy, true);
  txt(slide, "↓", 928, 242, 55, 65, 45, C.white, true);
  shape(slide, "roundRect", 795, 316, 328, 76, C.pale);
  txt(slide, "Review and save", 825, 335, 280, 40, 25, C.navy, true);
  txt(slide, "↓", 928, 401, 55, 65, 45, C.white, true);
  shape(slide, "roundRect", 795, 476, 328, 76, C.pale);
  txt(slide, "Track progress", 825, 495, 280, 40, 25, C.navy, true);
  note(slide, "Introduce the problem and the actual verified deployment status. Course assignment: https://uta.instructure.com/courses/282238/assignments/2405836");
}

// 2 · Problem and users
{
  const slide = base("Why JobTrack exists");
  card(slide, 70, 188, 390, 149, "The problem", "Job seekers manage many applications and lose track of dates, status, and next steps.", C.pale);
  card(slide, 70, 361, 390, 150, "The users", "Students, recent graduates, and anyone applying to multiple jobs or internships.");
  card(slide, 70, 534, 390, 118, "The outcome", "Discover leads and track applications in one place.", C.pale);
  shape(slide, "roundRect", 511, 184, 690, 475, C.white, C.line);
  await addImage(slide, path.join(root, "docs", "dashboard.png"), 532, 203, 648, 414,
    "JobTrack local dashboard with fictional demonstration records");
  txt(slide, "Local UI screenshot · fictional records", 541, 622, 615, 24, 16, C.muted);
  note(slide, "The submitted project proposal describes a tracker for company, title, salary and status. This local screenshot shows fictional records and is not cloud proof. Proposal is in the team handoff package.");
}

// 3 · User flow
{
  const slide = base("User workflow");
  const data = [
    ["1  Add", "Open the app, or click the extension on a supported JobPosting page."],
    ["2  Review draft", "Check company, role, salary, type, date, URL, and notes before saving."],
    ["3  Track", "Move an application from Saved to Applied, Interview, Offer, or Rejected."],
    ["4  Find and act", "Discover jobs; search, filter, sort, edit, or delete tracked entries."],
  ];
  data.forEach(([a,b], i) => card(slide, 70 + i * 300, 228, 274, 286, a, b, i % 2 ? C.white : C.pale));
  txt(slide, "Discover remote jobs with Remotive; optional JSearch covers more boards. The extension reads structured JobPosting data. JobTrack does not apply to employers.",
      89, 559, 1102, 80, 23, C.muted);
  note(slide, "Remotive discovery and structured-posting capture are separate features. JSearch requires a user-owned API key. See README.md for provider limits.");
}

// 4 · Architecture, built from editable shapes
{
  const slide = base("Private AWS architecture");
  shape(slide, "roundRect", 62, 179, 412, 431, C.white, C.line);
  txt(slide, "Authorized workstation", 85, 200, 363, 42, 26, C.navy, true);
  card(slide, 87, 270, 162, 150, "Posting", "JSON-LD\nExtension", C.pale);
  txt(slide, "→", 252, 307, 53, 62, 43, C.teal, true);
  card(slide, 307, 270, 145, 150, "App", "Review\nCRUD", C.pale);
  txt(slide, "↓", 351, 432, 53, 58, 40, C.teal, true);
  card(slide, 124, 485, 298, 120, "SSH tunnel", "Trusted client /32", C.gray);
  txt(slide, "→", 485, 387, 62, 62, 45, C.teal, true);
  shape(slide, "roundRect", 546, 179, 664, 431, C.pale, C.blue);
  txt(slide, "AWS account", 572, 200, 590, 42, 26, C.navy, true);
  card(slide, 570, 280, 293, 217, "EC2 · Python API", "Static UI + JSON API\nLoopback port 8000\nSSH from one /32 only", C.white);
  txt(slide, "→", 869, 347, 61, 62, 45, C.teal, true);
  card(slide, 930, 280, 251, 217, "Encrypted EBS", "SQLite database\nPersists stop/start", C.white);
  txt(slide, `${evidence.aws_verified ? "CloudFormation provisions" : "Planned: CloudFormation provisions"} · Private S3 holds source ZIP · sandbox myS3Role profile grants S3 access`,
      580, 531, 594, 64, 19, C.muted);
  note(slide, "Architecture source: deploy/cloudformation-sandbox.json. EC2 has a public IPv4 for bootstrap and SSH restricted to one trusted client /32. The web app listens on loopback only.");
}

// 5 · Logic and data
{
  const slide = base("Application logic and data");
  card(slide, 70, 190, 500, 410, "One applications table",
    "ID · company · title · location\nAnnual USD salary · employment type\nStatus · application date · URL · notes\nCreated and updated timestamps in UTC\nSQLite WAL; parameterized values", C.pale);
  const routes = [
    ["GET", "/api/health", "API and database check"],
    ["GET", "/api/jobs", "Discover job listings"],
    ["POST", "/api/applications", "Create record"],
    ["PUT", "/api/applications/{id}", "Replace editable fields"],
    ["DELETE", "/api/applications/{id}", "Delete record"],
  ];
  txt(slide, "JSON API", 622, 194, 500, 40, 30, C.navy, true);
  routes.forEach(([method, route, purpose], i) => {
    shape(slide, "roundRect", 614, 256 + i * 67, 580, 58, i % 2 ? C.white : C.pale, C.line);
    txt(slide, method, 629, 269 + i * 67, 95, 34, 19, C.blue, true);
    txt(slide, route, 723, 269 + i * 67, 280, 34, 18, C.navy, true);
    txt(slide, purpose, 1004, 269 + i * 67, 177, 34, 16, C.muted);
  });
  note(slide, "The app validates fields and restricts sort keys. API details and limits are documented in README.md. PUT is a full replacement, not a partial patch.");
}

// 6 · Cloud deployment
{
  const slide = base("Cloud deployment and access");
  const verified = !!evidence.aws_verified;
  const line = verified
    ? `Verified in ${evidence.region || "AWS region not recorded"} on ${evidence.instance_type || "instance type not recorded"}`
    : "AWS deployment pending verification in this draft";
  shape(slide, "roundRect", 70, 186, 1127, 108, verified ? C.pale : C.gray, C.line);
  txt(slide, line, 99, 212, 1050, 55, 30, C.navy, true);
  card(slide, 70, 326, 350, 250, "Provision", verified ?
    "CloudFormation creates EC2, encrypted EBS, and SSH restricted to one /32; it attaches myS3Role." :
    "Planned: CloudFormation would create EC2, encrypted EBS, and SSH restricted to one /32.", C.white);
  card(slide, 465, 326, 350, 250, "Connect", verified ?
    "An authorized user starts an SSH tunnel to forward local port 8000." :
    "Planned: an authorized user would start an SSH port forward.", C.pale);
  card(slide, 860, 326, 337, 250, "Verify", verified ?
    "Systemd, /api/health, cloud-backed CRUD, refresh, and persistence were checked." :
    "Pending: check systemd, health, cloud-backed CRUD, refresh, and persistence.", C.white);
  txt(slide, "The sandbox session is time-limited. The private demo has no public URL or user accounts. Back up data before instance or stack deletion.",
      83, 612, 1120, 58, 21, C.muted);
  note(slide, "Cloud deployment evidence includes stack events, SSH access, service status, health, and cloud-backed workflow. Local-only results are separate.");
}

// 7 · Verification
{
  const slide = base("Verification results");
  shape(slide, "roundRect", 70, 191, 326, 209, C.pale, C.line);
  txt(slide, "23", 100, 227, 160, 85, 67, C.blue, true);
  txt(slide, "Python tests", 102, 321, 253, 42, 24, C.navy, true);
  shape(slide, "roundRect", 429, 191, 326, 209, C.pale, C.line);
  txt(slide, "5", 459, 227, 160, 85, 67, C.blue, true);
  txt(slide, "extractor tests", 461, 321, 253, 42, 24, C.navy, true);
  card(slide, 788, 191, 410, 209, "Browser workflow", "Create · edit · filter · sort · refresh · delete", C.white);
  const extensionText = evidence.extension_verified
    ? "Installed extension verified on the bundled JobPosting fixture, through review, save, and refresh."
    : "Built-in browser verified draft review, save, edit, refresh, and deletion. Installed extension toolbar remains unverified.";
  card(slide, 70, 439, 1128, 169, "Capture check", extensionText, C.white);
  note(slide, "Tests: python3 -m unittest discover -s tests -v; node --test tests/extraction.test.cjs. The original midpoint browser QA is documented in docs/VERIFICATION.md. Update the installed extension claim only after observing it.");
}

// 8 · Measurements
{
  const slide = base("Performance evaluation");
  const shownMetrics = evidence.aws_verified ? metrics : localMetrics;
  if (!shownMetrics) {
    card(slide, 70, 201, 1128, 336, "AWS measurements pending",
      "The final chart will show median and p95 HTTP latency for health, list, and search. Method: 50 sequential GET requests per endpoint after 5 warmups through the SSM tunnel.", C.pale);
  } else {
    const entries = [["Health", "health"], ["List all", "list_all"], ["Search", "search_engineer"]];
    if (!evidence.aws_verified) txt(slide, "Localhost baseline only · cloud measurement pending", 74, 169, 1100, 35, 21, C.muted, true);
    const max = Math.max(...entries.map(([, k]) => shownMetrics.results[k].p95_ms)) || 1;
    entries.forEach(([label, key], i) => {
      const r = shownMetrics.results[key];
      const y = 210 + i * 120;
      txt(slide, label, 74, y, 190, 42, 25, C.navy, true);
      shape(slide, "roundRect", 262, y + 5, 690 * r.p95_ms / max, 36, C.light);
      shape(slide, "roundRect", 262, y + 5, 690 * r.median_ms / max, 36, C.teal);
      txt(slide, `median ${r.median_ms.toFixed(2)} ms · p95 ${r.p95_ms.toFixed(2)} ms`,
          965, y + 3, 300, 45, 18, C.muted);
    });
    txt(slide, evidence.aws_verified ?
      `${shownMetrics.requests_per_endpoint} sequential requests per endpoint · ${shownMetrics.database_records} records · ${evidence.instance_type} · ${evidence.region}` :
      `${shownMetrics.requests_per_endpoint} sequential requests per endpoint · ${shownMetrics.database_records} fictional records · localhost`,
        75, 591, 1120, 60, 21, C.muted);
  }
  note(slide, "Measurement source: evidence/performance-aws.json, produced by tools/benchmark.py. Includes client and SSH tunnel latency. It is a small single-user sample, not a load/scalability test.");
}

// 9 · Lessons and close
{
  const slide = base("Lessons and next steps");
  card(slide, 70, 189, 348, 358, "What we fixed", "Browser QA revealed a Reset-button conflict. Final API review found database connections left open. Both were repaired and tested.", C.pale);
  card(slide, 466, 189, 348, 358, "Current limits", "Single user, no login or public URL, no automated backup. Job discovery uses Remotive and optional JSearch; no machine learning.", C.white);
  card(slide, 862, 189, 337, 358, "Future work", "Add authentication and user isolation, managed backup/database, HTTPS hosting, monitoring, and broader extraction.", C.pale);
  txt(slide, evidence.roles || "Team roles: awaiting confirmation before final export", 75, 578, 1120, 65, 22, C.navy, true);
  note(slide, "Conclude with the observed final result and limitations. The pair are listed as equal co-developers at the user's direction.");
}

const buildDir = path.join(root, "work", "presentation-build");
await fs.mkdir(buildDir, { recursive: true });
for (const [index, slide] of deck.slides.items.entries()) {
  const png = await deck.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(buildDir, `slide-${String(index + 1).padStart(2, "0")}.png`),
                     new Uint8Array(await png.arrayBuffer()));
}
const output = draft ? path.join(buildDir, "Group42-JobTrack-DRAFT.pptx")
                     : path.join(root, "deliverables", "Group42-JobTrack.pptx");
await fs.mkdir(path.dirname(output), { recursive: true });
if (process.argv.includes("--debug-shapes")) {
  for (const [index, slide] of deck.slides.items.entries()) {
    for (const [j, item] of slide.shapes.items.entries()) {
      const p = item.position;
      if (p && (p.width < 0 || p.height < 0)) console.error("negative shape", index + 1, j, item.name, p.left, p.top, p.width, p.height);
    }
  }
}
await (await PresentationFile.exportPptx(deck)).save(output);
console.log(output);

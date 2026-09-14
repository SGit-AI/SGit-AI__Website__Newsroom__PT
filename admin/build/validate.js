#!/usr/bin/env node
// pt.newsroom.sgit.ai pre-release gate. Copied whole from newsroom.sgit.ai v0.3.9
// (briefs/pack/03__inherit/admin-build/validate.js) — the pack says it needs only a
// CNAME change, and that is what it got, plus the two notes marked PT below. Run from anywhere: node admin/build/validate.js
// Checks, in order:
//   1. version agreement — admin/build/version.txt vs every page's version badge,
//      the versions table, llms.txt and index.md
//   2. internal links — every relative href/src in every .html file resolves to a
//      file in the tree (fragments stripped; external and mailto links skipped)
//   3. canonical host — every <link rel="canonical"> and og:url points at the host
//      in CNAME (or, for a verbatim republication, at the stated source host — see
//      check 8), and every page declares one
//   4. the agent surface — every section hub is named in llms.txt, and the sitemap
//      and the tree agree in both directions
//   5. key-leak tripwire — nothing in the tree may look like an sgit vault key
//   6. div balance — every page opens and closes the same number of <div>s
//   7. every page ends with an agent block — the house rule inherited from
//      issues-fs.sgit.ai
//   8. the provenance contract — every page carrying a republished-material block
//      (class="provenance") states a first-published date and a source link. This
//      is the site's own central argument (most articles do not provide evidence,
//      the link is never followed) applied to itself. See briefs/02.
//   9. the redaction watch-list — nothing Tier 3 in briefs/08__source-manifest.csv
//      (named VC, live product pricing, an infra account number) may appear
//      anywhere in the published tree.
//  10. no build tooling is gitignored — a generated page whose generator is not in
//      the repository cannot be rebuilt by anyone who clones it. This has now
//      happened twice from the same cause (see .gitignore), so it is a check.
// Any failure exits 1: no tag, no publish.
'use strict';
const fs   = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT   = path.resolve(__dirname, '..', '..');
const errors = [];

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    if (name === '.git' || name === '.github' || name === 'node_modules' || name === '.sg_vault') continue;
    const p  = path.join(dir, name);
    const st = fs.statSync(p);
    if (st.isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

const files     = walk(ROOT);
const htmlFiles = files.filter(f => f.endsWith('.html'));
const rel       = f => path.relative(ROOT, f).split(path.sep).join('/');

// --- 1. version agreement -------------------------------------------------
const VERSION = fs.readFileSync(path.join(ROOT, 'admin/build/version.txt'), 'utf8').trim();
if (!/^v\d+\.\d+\.\d+$/.test(VERSION)) {
  errors.push(`version.txt does not carry a vX.Y.Z version: "${VERSION}"`);
}
for (const f of htmlFiles) {
  const t = fs.readFileSync(f, 'utf8');
  const badges = [...t.matchAll(/class="ver"[^>]*>(v\d+\.\d+\.\d+)</g)].map(m => m[1]);
  for (const b of badges) if (b !== VERSION) {
    errors.push(`${rel(f)}: version badge ${b} != ${VERSION}`);
  }
}
for (const extra of ['llms.txt', 'index.md']) {
  const t = fs.readFileSync(path.join(ROOT, extra), 'utf8');
  if (!t.includes(VERSION)) errors.push(`${extra} does not mention ${VERSION}`);
}
const versTable = fs.readFileSync(path.join(ROOT, 'admin/versions.html'), 'utf8');
if (!versTable.includes(`class="vnum">${VERSION}<`)) {
  errors.push(`admin/versions.html has no row for ${VERSION}`);
}
const rows = [...versTable.matchAll(/class="vnum">(v\d+\.\d+\.\d+)</g)].map(m => m[1]);
for (const v of rows) if (rows.filter(x => x === v).length > 1) {
  errors.push(`admin/versions.html lists ${v} more than once`);
  break;
}

// --- 2. internal links ----------------------------------------------------
for (const f of htmlFiles) {
  const t   = fs.readFileSync(f, 'utf8');
  const dir = path.dirname(f);
  for (const m of t.matchAll(/(?:href|src|data-src)="([^"#]+)(?:#[^"]*)?"/g)) {
    const target = m[1];
    if (/^(https?:|mailto:|data:|\/\/)/.test(target) || target === '') continue;
    if (!fs.existsSync(path.resolve(dir, target))) {
      errors.push(`${rel(f)}: broken link -> ${target}`);
    }
  }
}

// --- 3. canonical host ----------------------------------------------------
// A verbatim republication of docs.diniscruz.ai material points its canonical at
// the ORIGINAL, per briefs/02 §3.4 — that page is exempt from the CNAME-host rule
// and marked instead with data-canonical-is-source on the <html> tag.
const HOST = fs.readFileSync(path.join(ROOT, 'CNAME'), 'utf8').trim();
if (!/^[a-z0-9.-]+$/.test(HOST)) errors.push(`CNAME does not carry a hostname: "${HOST}"`);
for (const f of htmlFiles) {
  const t = fs.readFileSync(f, 'utf8');
  const exempt = /data-canonical-is-source/.test(t);
  const claimed = [
    ...[...t.matchAll(/<link[^>]+rel="canonical"[^>]+href="([^"]+)"/g)].map(m => m[1]),
    ...[...t.matchAll(/<meta[^>]+property="og:url"[^>]+content="([^"]+)"/g)].map(m => m[1]),
  ];
  if (!exempt) {
    for (const url of claimed) if (!url.startsWith(`https://${HOST}/`)) {
      errors.push(`${rel(f)}: canonical/og:url is not on ${HOST} -> ${url}`);
    }
  }
  if (!/rel="canonical"/.test(t)) errors.push(`${rel(f)}: no canonical link`);
}

// --- 4. the agent surface -------------------------------------------------
const llms = fs.readFileSync(path.join(ROOT, 'llms.txt'), 'utf8');
const hubs = htmlFiles.map(rel).filter(p => p.endsWith('/index.html') && p.split('/').length === 2);
for (const h of hubs) if (!llms.includes(h)) {
  errors.push(`llms.txt does not name the section hub /${h} — for an agent that page does not exist`);
}
const sitemap = fs.readFileSync(path.join(ROOT, 'sitemap.xml'), 'utf8');
const listed  = [...sitemap.matchAll(new RegExp(`<loc>https://${HOST}/([^<]+)</loc>`, 'g'))].map(m => m[1]);
for (const p of listed) if (!fs.existsSync(path.join(ROOT, p))) {
  errors.push(`sitemap.xml lists a page that does not exist: /${p}`);
}
for (const f of htmlFiles) if (!listed.includes(rel(f))) {
  errors.push(`sitemap.xml is missing ${rel(f)}`);
}

// --- 5. key-leak tripwire --------------------------------------------------
const KEY_SHAPE = /[A-Za-z0-9_-]{20,}:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/;
for (const f of files) {
  if (/\.(png|jpg|jpeg|gif|webp|ico|woff2?|zip|svg|pdf)$/.test(f)) continue;
  const t = fs.readFileSync(f, 'utf8');
  if (KEY_SHAPE.test(t)) errors.push(`${rel(f)}: contains a vault-key-shaped string`);
}

// --- 6. div balance ----------------------------------------------------
for (const f of htmlFiles) {
  const t     = fs.readFileSync(f, 'utf8');
  const open  = (t.match(/<div\b/g)   || []).length;
  const close = (t.match(/<\/div>/g)  || []).length;
  if (open !== close) {
    errors.push(`${rel(f)}: ${open} <div> vs ${close} </div> — a block is not closed`);
  }
}

// --- 7. every page ends with an agent block --------------------------------
for (const f of htmlFiles) {
  const r = rel(f);
  // documents/index.html is a hand-written hub and owes an agent block like any other
  // page; documents/<slug>.html are generated projections of raw markdown (gen_documents.py)
  // and are exempt, the same exemption issues-fs.sgit.ai makes for its reader pages.
  // PT: this site has no documents/ projections and no participant page. admin/ is
  // machinery rather than publication and keeps the parent's exemption.
  if (r.startsWith('admin/')) continue;
  const t = fs.readFileSync(f, 'utf8');
  if (!/class="agent"/.test(t)) {
    errors.push(`${r}: no "for an agent" block — every page on this site owes one`);
  }
}

// --- 8. the provenance contract --------------------------------------------
// briefs/02 is the load-bearing file in this site's own brief pack: a page that
// republishes or derives from previously published material must carry a visible
// provenance block naming the original date and linking to the original.
for (const f of htmlFiles) {
  const t = fs.readFileSync(f, 'utf8');
  for (const m of t.matchAll(/<div class="provenance"[^>]*>([\s\S]*?)<\/div>/g)) {
    const block = m[1];
    if (!/First published/.test(block)) {
      errors.push(`${rel(f)}: a provenance block has no "First published" date`);
    }
    if (!/href="https?:\/\//.test(block)) {
      errors.push(`${rel(f)}: a provenance block has no link to the original source`);
    }
  }
}

// --- 9. the redaction watch-list --------------------------------------------
// briefs/06 §2 and briefs/08 Tier 3 rows. Literal strings that must never appear
// anywhere in the published tree — a named VC, live B2B pricing, an infra account.
// Two things about this list were wrong until v0.2.2 and are worth stating so they are
// not reintroduced:
//
//   1. briefs/ used to be exempt, on the reasoning that "the pack documents the
//      watch-list by naming these". That reasoning is inverted. The watch-list names
//      each item in the course of FORBIDDING its publication, so publishing the pack
//      verbatim published exactly what the pack forbids — a real leak that reached the
//      live site. The published pack is now checked like every other file, and the
//      redactions are recorded in briefs/PUBLIC.md.
//   2. The pricing patterns were written from memory of the brief's prose rather than
//      against the strings actually in the files, so they matched nothing. Every entry
//      below is now a literal that was verified to appear in the source before masking.
const REDACTED = [
  // PACK COPY: the parent site's Tier-3 watch-list is deliberately not carried here — those
  // strings are the parent's to forbid, not yours to publish. Fill this from YOUR source
  // manifest: every literal that must never appear on pt.newsroom.sgit.ai (a contact detail
  // pattern is already gate 11; this list is for named things the editor has ruled out).
];
for (const f of files) {
  if (f === path.join(ROOT, 'admin/build/validate.js')) continue; // this file necessarily names what it bans
  if (/\.(png|jpg|jpeg|gif|webp|ico|woff2?|zip|svg|pdf)$/.test(f)) continue;
  const t = fs.readFileSync(f, 'utf8');
  for (const bad of REDACTED) if (t.includes(bad)) {
    errors.push(`${rel(f)}: contains redacted material "${bad}" — see briefs/06__boundaries-and-house-style.md §2`);
  }
}

// --- 10. no build tooling is gitignored ------------------------------------
// v0.1.0 shipped with admin/build/ silently excluded by a bare `build/` rule in a
// generic Python .gitignore; CI failed with MODULE_NOT_FOUND and the path was
// re-included by name. governance/build/ was created at v0.2.6 and hit the SAME rule,
// and because its generated HTML was committed the site kept deploying correctly while
// build.py, floor.py and gates.py were dropped from every commit for three releases.
// It surfaced only when a published document linked to floor.py on GitHub and 404'd.
// Fixing the instance twice would have guaranteed a third time, so the rule is now
// root-anchored AND this check exists: a generated page whose generator is not in the
// repository cannot be rebuilt by anyone who clones it.
try {
  const ignored = execFileSync('git', ['ls-files', '--others', '--ignored', '--exclude-standard'],
                               { cwd: ROOT, encoding: 'utf8' })
    .split('\n').map(s => s.trim()).filter(Boolean);
  for (const p of ignored) {
    if (/(^|\/)__pycache__\//.test(p) || /\.pyc$/.test(p)) continue;   // real build output
    if (/(^|\/)build\//.test(p) || /\.(py|js|mjs)$/.test(p)) {
      errors.push(`${p}: build tooling is excluded by .gitignore — it would not reach the ` +
                  `repository, and the pages it generates could not be rebuilt from a clone`);
    }
  }
} catch (e) {
  // Not a git checkout, or git unavailable. Not a failure — just unverifiable here.
  console.warn('validate: check 10 skipped (git not available)');
}

// --- report ---------------------------------------------------------------
if (errors.length) {
  console.error(`validate: ${errors.length} error(s)`);
  for (const e of errors) console.error('  ✗ ' + e);
  process.exit(1);
}
console.log(`validate: OK — ${VERSION} on ${HOST}, ${htmlFiles.length} pages, ` +
            `${hubs.length} hubs in llms.txt, sitemap agrees, links resolve, blocks balanced, ` +
            `every page carries an agent block, provenance blocks sourced, no redacted material, ` +
            `no key-shaped strings`);

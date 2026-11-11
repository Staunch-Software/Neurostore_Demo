import puppeteer from 'puppeteer';
import { preview } from 'vite';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

if (process.env.SKIP_PRERENDER === '1') {
  console.log('SKIP_PRERENDER=1: skipping prerender (local build only).');
  process.exit(0);
}

// The live site uses a self-signed certificate in this environment.
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distDir = path.resolve(__dirname, '../dist');

// Must match generateSlug() in src/pages/ProductDetails.jsx exactly
function generateSlug(text) {
  if (!text) return '';
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
}

// Windows Chrome path — adjust if yours differs
const WIN_CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const CHROME_PATH = process.env.CHROME_PATH || (fs.existsSync(WIN_CHROME) ? WIN_CHROME : undefined);

async function newPage(browser) {
  const p = await browser.newPage();
  await p.setRequestInterception(true);
  p.on('request', (req) => {
    const u = req.url();
    if (u.includes('google-analytics.com') || u.includes('googletagmanager.com') || u.includes('/api/track/view')) {
      req.abort();
    } else {
      req.continue();
    }
  });
  return p;
}

async function main() {
  console.log('Fetching product list from live API...');
  const res = await fetch('https://neurostore.in/api/products');
  if (!res.ok) throw new Error(`Failed to fetch products: ${res.status}`);
  const products = await res.json();
  console.log(`Fetched ${products.length} products`);

  let browser = null;
  let previewServer = null;
  let browserClosedNormally = false;

  try {
    console.log('Starting local preview server for dist/...');
    previewServer = await preview({
      preview: {
        port: 4173,
        proxy: {
          '/api': { target: 'https://neurostore.in', changeOrigin: true, secure: false },
        },
      },
    });
    const port = previewServer.config.preview.port;
    const baseUrl = `http://localhost:${port}`;

    browser = await puppeteer.launch({
      ...(CHROME_PATH ? { executablePath: CHROME_PATH } : {}),
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    browser.on('disconnected', () => {
      if (!browserClosedNormally) {
        console.error('\n!! Chrome disconnected/crashed unexpectedly !!');
      }
    });

    // ---------- Parallel rendering ----------
    const CONCURRENCY = Number(process.env.PRERENDER_CONCURRENCY) || 4;
    const RECYCLE_EVERY = 20; // per worker

    let success = 0;
    let failed = 0;
    let skipped = 0;
    let completed = 0;
    let consecutiveFails = 0;
    let fatalError = null;

    // Build the job queue (skip empty slugs and already-rendered pages)
    const queue = [];
    for (const product of products) {
      const slug = product.slug || generateSlug(product.name);
      if (!slug) { console.warn(`Skipping product with empty slug: ${product.id}`); continue; }

      const outDir = path.join(distDir, 'products', slug);
      const outFile = path.join(outDir, 'index.html');

      if (fs.existsSync(outFile)) {
        skipped++;
        completed++;
        continue;
      }
      queue.push({ slug, outDir, outFile });
    }

    let nextIndex = 0;

    async function renderOne(page, job) {
      const url = `${baseUrl}/products/${job.slug}`;
      for (let attempt = 1; attempt <= 3; attempt++) {
        try {
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
          await page.waitForSelector('h1.pd-title', { timeout: 15000 });
          break;
        } catch (e) {
          if (attempt === 3) throw e;
          await new Promise((r) => setTimeout(r, 2000));
        }
      }
      await new Promise((r) => setTimeout(r, 300));

      const html = await page.content();
      fs.mkdirSync(job.outDir, { recursive: true });
      fs.writeFileSync(job.outFile, html);
    }

    async function worker() {
      let page = await newPage(browser);
      let processed = 0;
      try {
        while (!fatalError) {
          const i = nextIndex++;
          if (i >= queue.length) break;
          const job = queue[i];

          try {
            await renderOne(page, job);
            success++;
            consecutiveFails = 0;
            console.log(`[${++completed}/${products.length}] OK  /products/${job.slug}`);
          } catch (err) {
            failed++;
            consecutiveFails++;
            console.error(`[${++completed}/${products.length}] FAIL /products/${job.slug} — ${err.message}`);
            if (consecutiveFails >= 5) {
              fatalError = new Error('5 pages failed in a row - aborting early');
              break;
            }
          }

          processed++;
          if (processed >= RECYCLE_EVERY) {
            processed = 0;
            await page.close().catch(() => {});
            page = await newPage(browser);
          }
        }
      } catch (err) {
        fatalError = fatalError || err;
      } finally {
        await page.close().catch(() => {});
      }
    }

    console.log(`Rendering ${queue.length} pages with ${CONCURRENCY} parallel workers...`);
    await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));

    if (fatalError) throw fatalError;

    console.log(`\nDone. ${success} rendered, ${skipped} already done, ${failed} failed.`);
  } finally {
    browserClosedNormally = true;

    if (browser) {
      await browser.close().catch(() => {});
    }

    if (previewServer?.httpServer) {
      await new Promise((resolve) => {
        previewServer.httpServer.close(() => resolve());
      }).catch(() => {});
    }
  }
}

main().catch((err) => {
  console.error('\nFATAL ERROR — script stopped:');
  console.error(err);
  process.exit(1);
});

process.on('unhandledRejection', (err) => {
  console.error('\nUNHANDLED REJECTION — this is likely why the process died silently before:');
  console.error(err);
  process.exit(1);
});
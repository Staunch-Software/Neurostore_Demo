// Shared by the storefront and scripts/prerender.mjs, so keep this free of browser-only imports.
import { isQuoteOnly } from './pricing.js';

export const slugify = (text) =>
    (text || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');

export const productSlug = (product) => product.slug || slugify(product.name);

const clean = (value) => (value == null ? '' : String(value).trim());
const isBlank = (value) => !clean(value) || /^(not specified|n\/a)$/i.test(clean(value));
const lowerFirst = (value) => value.charAt(0).toLowerCase() + value.slice(1);
const textOf = (product) => `${clean(product.family)} ${clean(product.name)}`;
const isEsu = (product) => /\bESU\b|Extended Security Updates/i.test(textOf(product));

const hash = (value) => {
    let result = 0;
    for (const char of String(value)) result = (result * 31 + char.charCodeAt(0)) >>> 0;
    return result;
};
const pick = (variants, seed) => variants[hash(seed) % variants.length];

const compareProducts = (a, b) =>
    clean(a.family).localeCompare(clean(b.family), undefined, { numeric: true }) ||
    clean(a.name).localeCompare(clean(b.name), undefined, { numeric: true });

/* ───────────────────────── Categories ───────────────────────── */

const adobe = (pattern) => (p) => p.brand === 'Adobe' && pattern.test(textOf(p));

export const CATEGORY_GROUPS = ['Microsoft', 'Adobe', 'Cybersecurity & Backup', 'AI Hardware'];

// Order matters: the first matching rule wins.
export const CATEGORIES = [
    { slug: 'sql-server-esu', group: 'Microsoft', title: 'SQL Server Extended Security Updates',
        blurb: 'Extended Security Updates for SQL Server versions that have passed end of support, listed by edition, licence type and coverage year.',
        test: (p) => isEsu(p) && /SQL/i.test(textOf(p)) },
    { slug: 'windows-server-esu', group: 'Microsoft', title: 'Windows Server Extended Security Updates',
        blurb: 'Extended Security Updates for Windows Server editions that have passed end of support, listed by core pack and coverage year.',
        test: (p) => isEsu(p) && /Windows Server|Win Server/i.test(textOf(p)) },
    { slug: 'windows-10-esu', group: 'Microsoft', title: 'Windows 10 ESU',
        blurb: 'Extended Security Updates for Windows 10 devices, listed by edition and coverage year.',
        test: (p) => isEsu(p) && /Windows 10/i.test(textOf(p)) },
    { slug: 'windows-server-cals', group: 'Microsoft', title: 'Windows Server CALs',
        blurb: 'Client Access Licences, Remote Desktop Services and Rights Management licences and external connectors for Windows Server, in User and Device variants.',
        test: (p) => /Windows/i.test(clean(p.family)) && /CAL|Connector|Remote Desktop/i.test(clean(p.family)) },
    { slug: 'windows-server', group: 'Microsoft', title: 'Windows Server & System Center',
        blurb: 'Windows Server Standard and Datacenter core licence packs and System Center licences.',
        test: (p) => /Windows Server (Standard|Data Center) Core|System Center/i.test(clean(p.family)) },
    { slug: 'sql-server', group: 'Microsoft', title: 'SQL Server',
        blurb: 'SQL Server core licence packs, editions and Client Access Licences, plus related data products.',
        test: (p) => /SQL Server|Azure SQL/i.test(clean(p.family)) },
    { slug: 'exchange-server', group: 'Microsoft', title: 'Exchange Server',
        blurb: 'Exchange Server 2019 Standard and Enterprise Client Access Licences in User and Device variants.',
        test: (p) => /Exchange Server/i.test(clean(p.family)) },
    { slug: 'sharepoint-server', group: 'Microsoft', title: 'SharePoint Server',
        blurb: 'SharePoint Server 2019 Standard and Enterprise Client Access Licences in User and Device variants.',
        test: (p) => /SharePoint/i.test(clean(p.family)) },
    { slug: 'skype-for-business-server', group: 'Microsoft', title: 'Skype for Business Server',
        blurb: 'Skype for Business Server 2019 Standard, Plus and Enterprise Client Access Licences in User and Device variants.',
        test: (p) => /Skype for Business/i.test(clean(p.family)) },
    { slug: 'project-server', group: 'Microsoft', title: 'Project Server',
        blurb: 'Project Server 2019 and the Project Server User and Device CALs that give people access to it.',
        test: (p) => /Project Server/i.test(clean(p.family)) },
    { slug: 'biztalk-server', group: 'Microsoft', title: 'BizTalk Server',
        blurb: 'BizTalk Server 2020 Branch, Standard and Enterprise editions for application and B2B integration.',
        test: (p) => /BizTalk/i.test(clean(p.family)) },
    { slug: 'windows-desktop', group: 'Microsoft', title: 'Windows 10 & Windows 11',
        blurb: 'Windows 10 and Windows 11 licences, including Pro, Enterprise LTSC and IoT editions and upgrade licences.',
        test: (p) => /Windows 1[01]/i.test(textOf(p)) },
    { slug: 'office-ltsc', group: 'Microsoft', title: 'Office LTSC 2024',
        blurb: 'Office LTSC 2024 suites and individual apps such as Word, Excel, PowerPoint, Outlook and Access, for Windows and Mac.',
        test: (p) => /Office LTSC|Word LTSC|Excel LTSC|PowerPoint LTSC|Outlook LTSC|Access LTSC/i.test(clean(p.family)) },
    { slug: 'project-visio-visual-studio', group: 'Microsoft', title: 'Project, Visio & Visual Studio',
        blurb: 'Project, Visio and Visual Studio licences for planning, diagramming and development teams.',
        test: (p) => /Project (Standard|Professional)|Visio|Visual Studio/i.test(clean(p.family)) },
    { slug: 'backup-and-recovery', group: 'Cybersecurity & Backup', title: 'Backup & Disaster Recovery',
        blurb: 'Backup, disaster recovery, email archiving and file protection services, quoted to fit your environment.',
        test: (p) => clean(p.family) === 'Backup Solutions' },
    { slug: 'cybersecurity-services', group: 'Cybersecurity & Backup', title: 'Cybersecurity Services',
        blurb: 'Endpoint security, SaaS security and security awareness training services, quoted on request.',
        test: (p) => clean(p.family) === 'Cybersecurity Services' },
    { slug: 'it-operations-services', group: 'Cybersecurity & Backup', title: 'IT Operations Services',
        blurb: 'Remote monitoring and management (RMM) and professional service automation (PSA) services, quoted on request.',
        test: (p) => clean(p.family) === 'IT Operations Services' },
    { slug: 'ai-workstations', group: 'AI Hardware', title: 'AI Workstations',
        blurb: 'AI-ready computing hardware, including the Ai PC M5 mini workstation.',
        test: (p) => /^ai pc$/i.test(clean(p.brand)) },
    { slug: 'adobe-acrobat-sign', group: 'Adobe', title: 'Adobe Acrobat Sign',
        blurb: 'Acrobat Sign e-signature solutions for business, enterprise and small business, including transaction-based and Aadhaar signing offers.',
        test: adobe(/Acrobat Sign/i) },
    { slug: 'adobe-acrobat-pdf', group: 'Adobe', title: 'Adobe Acrobat & PDF Services',
        blurb: 'Acrobat Pro, Standard and Studio, the AI Assistant for Acrobat and Acrobat Services API for teams and enterprise.',
        test: adobe(/Acrobat/i) },
    { slug: 'adobe-creative-cloud', group: 'Adobe', title: 'Adobe Creative Cloud',
        blurb: 'Creative Cloud All Apps, Pro and Pro Plus plans for teams and enterprise.',
        test: adobe(/Creative Cloud|CC Standard/i) },
    { slug: 'adobe-web-and-servers', group: 'Adobe', title: 'Adobe Web & Server Products',
        blurb: 'Dreamweaver, ColdFusion and InDesign Server for web development and server-side publishing.',
        test: adobe(/ColdFusion|Dreamweaver|InDesign Server/i) },
    { slug: 'adobe-elearning-technical', group: 'Adobe', title: 'Adobe E-Learning & Technical Communication',
        blurb: 'Captivate, FrameMaker, RoboHelp and Technical Suite for e-learning and technical documentation.',
        test: adobe(/Captivate|FrameMaker|RoboHelp|Technical Suite/i) },
    { slug: 'adobe-video-audio', group: 'Adobe', title: 'Adobe Video, Audio & Animation',
        blurb: 'Premiere, After Effects, Audition and Animate for video, audio and animation work.',
        test: adobe(/Premiere|After Effects|Audition|Animate/i) },
    { slug: 'adobe-photo-imaging', group: 'Adobe', title: 'Adobe Photoshop & Lightroom',
        blurb: 'Photoshop, Photoshop Elements and Lightroom for photo editing and imaging.',
        test: adobe(/Photoshop|Lightroom|PHSP/i) },
    { slug: 'adobe-design-layout', group: 'Adobe', title: 'Adobe Design & Layout',
        blurb: 'Illustrator, InDesign, InCopy, Dimension, Adobe XD, Fresco, Express and Substance 3D for design and layout.',
        test: adobe(/Illustrator|InDesign|InCopy|Dimension|\bXD\b|Fresco|Express|Substance/i) },
    { slug: 'adobe-stock-and-credits', group: 'Adobe', title: 'Adobe Stock, Firefly & Credits',
        blurb: 'Adobe Stock plans, stock credit packs, Firefly plans and monthly generative credits.',
        test: adobe(/Stock|Credit|Firefly/i) },
    { slug: 'other-products', group: 'Microsoft', title: 'Other Products',
        blurb: 'Other products available from Neurostore.',
        test: () => true },
];

// Shown in the menu, footer and home page. Order is the display order.
export const FEATURED_CATEGORY_SLUGS = [
    'windows-server', 'windows-server-cals', 'sql-server', 'windows-10-esu', 'project-server', 'office-ltsc',
    'adobe-acrobat-pdf', 'adobe-creative-cloud', 'adobe-acrobat-sign',
    'backup-and-recovery', 'cybersecurity-services',
];

export const getCategoryBySlug = (slug) => CATEGORIES.find((category) => category.slug === slug);
export const getCategory = (product) => CATEGORIES.find((category) => category.test(product));

const indexCache = new WeakMap();

// Map of category slug -> { category, products } with products sorted by family then name.
export const getCategoryIndex = (products) => {
    let index = indexCache.get(products);
    if (index) return index;
    index = new Map();
    products.forEach((product) => {
        const category = getCategory(product);
        if (!index.has(category.slug)) index.set(category.slug, { category, products: [] });
        index.get(category.slug).products.push(product);
    });
    index.forEach((entry) => entry.products.sort(compareProducts));
    indexCache.set(products, index);
    return index;
};

// Categories that actually contain products, in CATEGORIES order.
export const getCategoryList = (products) => {
    const index = getCategoryIndex(products);
    return CATEGORIES.filter((category) => index.has(category.slug)).map((category) => index.get(category.slug));
};

/* ───────────────────────── Related products ───────────────────────── */

// Alternating neighbours on either side, wrapping round, so every product in a long list gets linked to.
const ringNeighbours = (list, index, count) => {
    const result = [];
    const size = list.length;
    for (let step = 1; result.length < count && step < size; step++) {
        const after = (index + step) % size;
        const before = (index - step + size) % size;
        result.push(list[after]);
        if (result.length < count && before !== after) result.push(list[before]);
    }
    return result;
};

export const getRelatedProducts = (product, products, limit = 6) => {
    const entry = getCategoryIndex(products).get(getCategory(product).slug);
    if (!entry) return [];
    const result = [];
    const seen = new Set([product.id]);
    const add = (items) => items.forEach((item) => {
        if (result.length < limit && !seen.has(item.id)) {
            seen.add(item.id);
            result.push(item);
        }
    });

    const sameFamily = entry.products.filter((item) => item.family === product.family);
    const familyIndex = sameFamily.findIndex((item) => item.id === product.id);
    if (familyIndex >= 0) add(ringNeighbours(sameFamily, familyIndex, limit));

    const categoryIndex = entry.products.findIndex((item) => item.id === product.id);
    if (categoryIndex >= 0) add(ringNeighbours(entry.products, categoryIndex, limit * 2));
    return result;
};

/* ───────────────────────── Product content ───────────────────────── */

const termInfo = (product) => {
    const term = clean(product.term || product.additionalInfo?.Term);
    if (/3 Years?/i.test(term)) return { type: 'subscription', label: '3-year (triennial)', phrase: '3-year (triennial) subscription' };
    if (/1 Year/i.test(term)) return { type: 'subscription', label: '1-year (annual)', phrase: '1-year (annual) subscription' };
    if (/12 Months/i.test(term)) return { type: 'subscription', label: '12-month', phrase: '12-month subscription term' };
    if (/Perpetual/i.test(term)) return { type: 'perpetual', label: 'perpetual', phrase: 'perpetual licence' };
    return { type: 'other', label: lowerFirst(term || 'subscription'), phrase: lowerFirst(term || 'subscription term') };
};

const coverageOf = (product) => {
    const match = clean(product.name).match(/\(([^)]*\d{4}[^)]*)\)/);
    return match ? match[1].replace(/^Coverage\s+/i, '') : '';
};

const microsoftKind = (product) => {
    const text = textOf(product);
    if (isEsu(product)) return 'esu';
    if (/External Connector/i.test(text)) return 'connector';
    if (/\bCAL\b|Remote Desktop Services/i.test(text)) {
        if (/Device/i.test(product.name)) return 'cal-device';
        if (/User/i.test(product.name)) return 'cal-user';
        return 'cal';
    }
    if (/\bCores?\b/i.test(text)) return 'core';
    if (/Upgrade/i.test(text)) return 'upgrade';
    if (/Windows (10|11)/i.test(text)) return 'desktop';
    if (/LTSC|Visio|Project|Visual Studio/i.test(text)) return 'app';
    if (/Server|BizTalk|Azure/i.test(text)) return 'server';
    return 'software';
};

const cleanUnit = (value) => clean(value).replace(/\/+$/, '');

const esuTarget = (family) =>
    clean(family).replace(/^Extended Security Updates for\s+/i, '').replace(/\s+ESU$/i, '');

// Drops the bracketed coverage dates, which the copy states separately.
const esuName = (product) => clean(product.name).replace(/\s*\([^)]*\)/g, '').replace(/\s+/g, ' ').trim();

const row = (label, value) => (isBlank(value) ? null : [label, clean(value)]);

const microsoftContent = (product, category) => {
    const info = product.additionalInfo || {};
    const kind = microsoftKind(product);
    const term = termInfo(product);
    const name = kind === 'esu' ? esuName(product) : product.name;
    const target = kind === 'esu' ? esuTarget(product.family) : '';
    const seed = `${product.id}-${name}`;
    const quote = isQuoteOnly(product);
    const serverProduct = clean(product.family).replace(/\s+CAL\b/i, '');
    const coreCount = (name.match(/(\d+)\s*Core/i) || [])[1];
    const coverage = coverageOf(product);
    const termLine = term.type === 'perpetual' ? 'a perpetual licence' : `a ${term.phrase}`;

    const intros = {
        'cal-user': [
            `${name} is the user-based Client Access Licence for ${serverProduct}. One User CAL lets a single named user connect to the licensed server from any number of devices, which suits organisations where staff move between desktops, laptops and phones. This listing is ${termLine}.`,
            `Choose ${name} when you want to license people rather than machines. A User CAL covers one user's access to ${serverProduct} on whichever devices they use, and this version is ${termLine}.`,
            `For teams that use more than one device each, ${name} grants one user access to ${serverProduct}. It is a Client Access Licence only, and is offered here as ${termLine}.`,
        ],
        'cal-device': [
            `${name} is the device-based Client Access Licence for ${serverProduct}. One Device CAL covers a single PC or device that connects to the licensed server, no matter how many people use it, which suits shared workstations and shift-based teams. This listing is ${termLine}.`,
            `Choose ${name} when machines, not individuals, are what you need to license. A Device CAL covers one device's access to ${serverProduct} for any number of users, and this version is ${termLine}.`,
            `For shared PCs, kiosks and front-desk machines, ${name} licenses the device instead of the person. It is a Client Access Licence only, offered here as ${termLine}.`,
        ],
        cal: [
            `${name} is a Client Access Licence for ${serverProduct}. It grants access rights to the licensed server rather than the server software itself, and is offered here as ${termLine}.`,
            `${name} covers client access to ${serverProduct}. Pair it with a licensed server to give your users or devices the right to connect; this version is ${termLine}.`,
            `If you already run ${serverProduct}, ${name} adds the access licence your users or devices need. It is listed as ${termLine}.`,
        ],
        connector: [
            `${name} is an external connector licence that allows ${lowerFirst(clean(product.family))} to be accessed by people outside your organisation, such as customers and partners, without licensing each one individually. It is offered here as ${termLine}.`,
            `Use ${name} when external users, for example customers or partners, need to reach your server. A connector licence covers that outside access for the licensed server, and this listing is ${termLine}.`,
            `${name} suits organisations that publish server resources to external users. It licenses the licensed server for external access and is available as ${termLine}.`,
        ],
        core: [
            `${name} is a ${coreCount ? `${coreCount}-core ` : ''}licence pack for ${clean(product.family)}. Core packs are added together until every core on the server you are licensing is covered, which makes them the usual choice for data centre and virtualised hosts. This listing is ${termLine}.`,
            `Size your server licence with ${name}: each pack${coreCount ? ` covers ${coreCount} cores` : ' covers a set number of cores'} of ${clean(product.family)}. Buy as many packs as the host needs; this version is ${termLine}.`,
            `${name} licenses server cores${coreCount ? ` in blocks of ${coreCount}` : ''} for ${clean(product.family)}. It suits teams that need predictable per-core licensing and is offered as ${termLine}.`,
        ],
        esu: [
            `${name} keeps ${target} deployments that are past end of support protected with critical security updates${coverage ? ` for ${coverage}` : ' for the listed coverage period'}. It is meant for organisations that cannot migrate yet and need cover in the meantime.`,
            `Not ready to upgrade? ${name} gives ${target} critical security updates${coverage ? ` during ${coverage}` : ' for the listed coverage period'}, buying time for a planned migration.`,
            `${name} is Extended Security Updates cover${coverage ? ` for ${coverage}` : ''} for ${target}. It adds security updates after standard support ends; it does not add new features.`,
        ],
        upgrade: [
            `${name} is an upgrade licence for organisations that already hold a qualifying Windows licence and want to move to ${clean(product.family)}. It is offered here as ${termLine}.`,
            `Move existing devices up with ${name}. This upgrade licence applies to devices that already have a qualifying base licence, and is listed as ${termLine}.`,
            `${name} suits businesses standardising on ${clean(product.family)} across devices they already own. It is an upgrade licence, available as ${termLine}.`,
        ],
        desktop: [
            `${name} is a ${clean(product.family)} licence for business devices. It is sold under the Microsoft commercial licensing programme as ${termLine}.`,
            `Standardise your desktops on ${clean(product.family)} with ${name}. The licence is a commercial one, listed as ${termLine}.`,
            `${name} gives a business device a ${clean(product.family)} licence under the commercial programme, offered here as ${termLine}.`,
        ],
        app: [
            `${name} is a ${term.type === 'perpetual' ? 'one-time purchase' : 'subscription'} licence for ${clean(product.family)}, listed as ${termLine}. It is aimed at business users who need the application on a managed device.`,
            `Add ${clean(product.family)} to your managed desktops with ${name}. The licence is commercial and is offered as ${termLine}.`,
            `${name} suits teams that need ${clean(product.family)} installed and supported under a commercial licence. It is available as ${termLine}.`,
        ],
        server: [
            `${name} is a server product licence for ${clean(product.family)}, offered as ${termLine}. It is aimed at IT teams building or maintaining that server platform.`,
            `Deploy ${clean(product.family)} with ${name}. This listing is the server licence and is available as ${termLine}.`,
            `${name} licenses ${clean(product.family)} for your server environment and is listed as ${termLine}.`,
        ],
        software: [
            `${name} is a ${clean(product.family)} licence sold under the Microsoft commercial programme as ${termLine}.`,
            `${name} gives your organisation a licensed copy of ${clean(product.family)}, offered as ${termLine}.`,
            `Buy ${name} to license ${clean(product.family)} for business use. It is listed as ${termLine}.`,
        ],
    };

    const faqs = [];
    const needsServer = `${name} gives access rights only. A separately licensed server running ${serverProduct} is still required.`;
    if (kind === 'cal-user' || kind === 'cal-device' || kind === 'cal') {
        faqs.push({
            q: 'What is the difference between a User CAL and a Device CAL?',
            a: `A User CAL licenses one person to access the server from any number of devices. A Device CAL licenses one device that any number of people can use. User CALs usually suit staff who work across several devices, while Device CALs suit shared PCs, kiosks and shift-based workstations. This page is for ${kind === 'cal-device' ? 'the Device CAL' : kind === 'cal-user' ? 'the User CAL' : 'the CAL'} for ${serverProduct}.`,
        });
        faqs.push({ q: `Does ${name} include the server software?`, a: needsServer });
    } else if (kind === 'core') {
        faqs.push({
            q: `What does a ${coreCount ? `${coreCount}-core ` : ''}licence pack cover?`,
            a: `${coreCount ? `One pack licenses ${coreCount} cores` : 'One pack licenses a set number of cores'} of ${clean(product.family)}. The number of packs you need depends on the cores in the server you are licensing, so add packs until all required cores are covered. Our team can help you size this.`,
        });
        faqs.push({
            q: `Do I need CALs as well as ${name}?`,
            a: /Windows Server/i.test(product.family)
                ? 'Yes. Windows Server licensed per core also needs Client Access Licences for each user or device that connects.'
                : /SQL/i.test(product.family)
                    ? 'SQL Server licensed per core does not use CALs for access. Confirm the licensing model for your deployment with our team before ordering.'
                    : 'CAL requirements depend on the product and licensing model. Our team can confirm what your deployment needs.',
        });
    } else if (kind === 'esu') {
        faqs.push({
            q: 'What are Extended Security Updates?',
            a: `Extended Security Updates provide critical security updates for eligible products after their end-of-support date, for a limited coverage period.${coverage ? ` ${name} covers ${coverage}.` : ''} They are for security fixes and do not add new features.`,
        });
        faqs.push({
            q: `Do I need earlier years of coverage before buying ${name}?`,
            a: 'ESU coverage is generally cumulative, so earlier years may need to be covered first. Our team can confirm the requirement for this product before you order.',
        });
    } else if (kind === 'upgrade') {
        faqs.push({
            q: `Who is ${name} for?`,
            a: `It is for devices that already hold a qualifying base licence and need to be upgraded to ${clean(product.family)}. Confirm eligibility with our team before purchase.`,
        });
        faqs.push({
            q: 'Is this a full licence or an upgrade?',
            a: `${name} is an upgrade licence, so it depends on the device already being licensed. It does not replace the need for a valid base licence.`,
        });
    } else if (kind === 'connector') {
        faqs.push({
            q: 'When do I need an external connector?',
            a: `An external connector is for situations where people outside your organisation, such as customers or partners, access the licensed server. It avoids licensing each outside user or device separately. Confirm your scenario with our team.`,
        });
        faqs.push({ q: `Does ${name} replace the server licence?`, a: `No. ${name} covers external access only. The server itself must still be licensed.` });
    } else if (/LTSC/i.test(name)) {
        faqs.push({
            q: 'What does LTSC mean?',
            a: `LTSC stands for Long-Term Servicing Channel. ${name} is a fixed-version release that receives security fixes but not new features, which suits devices that need a stable, predictable setup.`,
        });
        faqs.push({
            q: `Is ${name} a subscription?`,
            a: term.type === 'perpetual'
                ? `No. ${name} is a perpetual licence: you pay once for this version rather than renewing a subscription.`
                : `${name} is offered as a ${term.phrase}, so it needs to be renewed when the term ends.`,
        });
    } else {
        faqs.push({
            q: `Is ${name} a perpetual licence or a subscription?`,
            a: term.type === 'perpetual'
                ? `${name} is listed as a perpetual licence, bought once for this version.`
                : `${name} is listed as a ${term.phrase}.`,
        });
        faqs.push({
            q: `Who is ${name} for?`,
            a: `It is a commercial licence for ${clean(product.family)}, intended for business and organisational use rather than personal use.`,
        });
    }

    if (term.type === 'subscription') {
        faqs.push({
            q: `What happens when the ${term.label} term ends?`,
            a: `${name} is a ${term.phrase}. Renew before the term ends to stay licensed, or ask our team to set up a renewal reminder.`,
        });
    } else if (kind !== 'esu') {
        faqs.push({
            q: `How long does ${name} last?`,
            a: `${name} is a perpetual licence for the listed version, so it does not expire. Updates follow Microsoft's support policy for that version.`,
        });
    }

    if (quote) {
        faqs.push({
            q: `Can I get a price for ${name}?`,
            a: `${name} is sold on a quote basis. Use the Request Quote or Call button on this page and our team will confirm pricing and availability.`,
        });
    } else {
        faqs.push({
            q: `How is ${name} delivered, and does the price include GST?`,
            a: `${isBlank(info.Delivery) ? 'It is delivered digitally by email.' : `Delivery method listed: ${info.Delivery}.`} Your licence key and setup details are sent to the email address on your order. The listed price is before GST; 18% GST and the total payable are shown on this page.`,
        });
    }

    const delivery = [
        row('Delivery', info.Delivery),
        row('Licence type', info['License Type']),
        row('Licence term', info.Term || product.term),
        row('Licensed per', cleanUnit(info['Purchase Unit'])),
        row('Programme', info.Agreement),
        row('Segment', info.Segment),
        row('Support & updates', info['Support & Updates']),
        row('Part number', info['Part Number']),
        row('Pricing', quote ? 'Price on request' : 'Listed price excludes 18% GST'),
    ].filter(Boolean);

    const deliveryNote = quote
        ? `Delivery and activation steps for ${name} are confirmed in your quotation.`
        : kind.startsWith('cal') || kind === 'connector'
            ? `${name} is delivered digitally. Remember that it grants access rights and must be used with a licensed server.`
            : `${name} is delivered digitally, so there is nothing to ship. Your licence details are emailed once the order is confirmed.`;

    return { categoryTitle: category.title, intro: pick(intros[kind], seed), faqs, delivery, deliveryNote };
};

const parseLevel = (level) => {
    const match = clean(level).match(/Level\s*(\d+)\s*([\d,]+\s*-\s*[\d,]+|[\d,]+\+)?\s*(?:\(([^)]*)\))?/i);
    if (!match) return null;
    return { number: match[1], band: clean(match[2]).replace(/\s+/g, ' '), note: clean(match[3]) };
};

const ADOBE_TYPES = {
    'Subscription New': 'new subscription',
    'Transaction New': 'transaction-based',
    'Enterprise Hosted Subscription New': 'hosted enterprise subscription',
    'Enterprise Consumption': 'enterprise credit-pack',
    'Team Consumption': 'team credit-pack',
    'Hosted Subscription': 'hosted subscription',
    'Term License': 'term licence',
    'Feature Restricted Term License': 'feature-restricted term licence',
};

const adobeContent = (product, category) => {
    const info = product.additionalInfo || {};
    const family = clean(product.family);
    const seed = `${product.id}-${product.name}`;
    const level = parseLevel(info['Level Detail']);
    const typeLabel = ADOBE_TYPES[clean(info['Software Type'])] || 'volume licensing';
    const unit = cleanUnit(info['Purchase Unit']) || 'user';
    const unitLower = /^named$/i.test(unit) ? 'named user'
        : /^1 user$/i.test(unit) ? 'user'
            : lowerFirst(unit.replace(/^per\s+/i, ''));
    const segment = clean(info.Segment) || 'Commercial';
    const isEdu = /Education/i.test(segment) || /EDU/i.test(clean(info['Additional Detail']));
    const audience = /for teams/i.test(family) ? 'small and mid-sized teams'
        : /for enterprise/i.test(family) || /Edition \d/i.test(family) ? 'larger organisations' : 'organisations';
    const duration = clean(info.Term || product.term);
    const termText = /12 Months/i.test(duration) ? 'a 12-month term' : `the ${lowerFirst(duration || 'subscription term')}`;
    const detail = clean(info['Additional Detail']);
    const offerNote = detail && !/^standard offering$/i.test(detail) && detail.length <= 90 && !/First Order Date/i.test(detail) ? detail : '';
    const bandText = level?.band ? `the ${level.band} quantity band` : level ? `pricing level ${level.number}` : 'the standard pricing level';
    const levelText = level ? `Level ${level.number}${level.band ? ` (${level.band})` : ''}${level.note ? `, ${level.note}` : ''}` : 'standard level';
    const platform = clean(info['Operating System']);
    const language = clean(info.Language);
    const programme = segment.replace(/\s*-\s*/g, ', ').toLowerCase();
    const partNo = clean(product.partNumber || info['Part Number']);
    const levelShort = level ? `Level ${level.number}${level.band ? ` (${level.band})` : ''}` : '';
    const isCommit = /3 year commit/i.test(`${segment} ${clean(info['Level Detail'])}`);
    // Compact label for sentences; the full product name is already the page heading.
    const name = [family, isEdu ? 'Education' : '', levelShort].filter(Boolean).join(' - ');

    const intros = [
        `${family} (part number ${partNo}) is an Adobe ${typeLabel} offer priced for ${bandText} under the ${programme} programme. It is licensed per ${unitLower} for ${termText}${offerNote ? ` and carries the note "${offerNote}"` : ''}, and is aimed at ${audience}.`,
        `Looking for ${family} for ${audience}? This listing is the ${levelText} ${programme} offer, part number ${partNo}: an Adobe ${typeLabel} product licensed per ${unitLower} for ${termText}${offerNote ? ` (${offerNote})` : ''}.`,
        `${family} from Adobe, in the ${programme} programme at ${levelText}. Part number ${partNo} is an Adobe ${typeLabel} offer licensed per ${unitLower}, running for ${termText}${platform && !/other|n\/a/i.test(platform) ? ` and supporting ${platform}` : ''}${language ? ` in ${language}` : ''}.`,
    ];

    const faqs = [];
    faqs.push({
        q: `What does ${levelShort || 'the standard level'} mean for ${family}?`,
        a: level
            ? `Adobe prices volume licences in tiers. This part number is listed for ${bandText}${level.note ? ` (${level.note})` : ''}, so the tier that applies depends on how many licences you buy. Our team confirms the right tier in your quotation.`
            : `This listing is priced at the standard level for ${family}. Our team confirms the tier that applies to your quantity in your quotation.`,
    });
    faqs.push({
        q: `Can I get a price for ${name}?`,
        a: `${name} is sold on a quote basis and no price is shown online. Use the Request Quote or Call button on this page, mention part number ${clean(product.partNumber || info['Part Number'])}, and our team will confirm pricing, availability and delivery.`,
    });
    faqs.push({
        q: isEdu ? 'Who can buy the education version?' : isCommit ? `What does the three-year commit mean for ${family}?` : `Who is the ${programme} version for?`,
        a: isEdu
            ? `Education offers are intended for qualifying educational institutions, staff or students${offerNote ? `, here marked "${offerNote}"` : ''}. Eligibility is typically verified before an order is accepted, and our team will confirm it in your quotation.`
            : isCommit
                ? 'This listing is part of Adobe\'s three-year commitment programme, which commits you to a multi-year term in return for its pricing level. Our team will explain the commitment terms in your quotation.'
                : `The ${programme} programme is for business and organisational purchases. Our team confirms the programme terms that apply to this listing in your quotation.`,
    });
    const typeNote = {
        'Transaction New': `${name} is a transaction-based offer, so usage is counted in transactions rather than by named user. Ask our team how transactions are counted and what happens when you need more.`,
        'Enterprise Consumption': `${name} is a credit-pack offer. Credits are used up as the associated Adobe services are used, so choose a pack size that matches your expected usage.`,
        'Team Consumption': `${name} is a credit-pack offer. Credits are used up as the associated Adobe services are used, so choose a pack size that matches your expected usage.`,
        'Term License': `${name} is a term licence, so it is time-limited and needs to be renewed when the term ends.`,
        'Feature Restricted Term License': `${name} is a feature-restricted term licence: it is time-limited and may not include every feature of the full product.`,
        'Hosted Subscription': `${name} is a hosted subscription, which means the service is hosted by Adobe and you pay per ${unitLower} for the term.`,
        'Enterprise Hosted Subscription New': `${name} is a hosted enterprise subscription, which means the service is hosted by Adobe and you pay per ${unitLower} for the term.`,
    }[clean(info['Software Type'])];
    faqs.push({
        q: typeNote ? `How does the ${typeLabel} model work for ${name}?` : `How long does ${name} last?`,
        a: typeNote || `${name} runs for ${termText}. Renew before it ends to stay licensed, or ask our team to set up a renewal reminder.`,
    });
    faqs.push({
        q: `Are other tiers of ${family} available?`,
        a: `Yes. ${family} is listed in several quantity tiers, terms and programmes. Use the Related products section below or browse ${category.title} to compare them.`,
    });

    const delivery = [
        row('Pricing', 'Price on request (quote-based)'),
        row('Delivery', info.Delivery),
        row('Licence type', info['License Type']),
        row('Programme', `${segment}${info.Agreement ? ` (${info.Agreement})` : ''}`),
        row('Pricing level', clean(info['Level Detail'])),
        row('Licence term', duration),
        row('Licensed per', unit),
        row('Platform', platform && !/^other$/i.test(platform) ? platform : ''),
        row('Language', language),
        row('Support & updates', info['Support & Updates']),
        row('Part number', info['Part Number']),
    ].filter(Boolean);

    return {
        categoryTitle: category.title,
        intro: pick(intros, seed),
        faqs,
        delivery,
        deliveryNote: `Pricing, availability and delivery for ${name} are confirmed in your quotation. Licence details are sent once the order is confirmed.`,
    };
};

const serviceContent = (product, category) => {
    const info = product.additionalInfo || {};
    const name = product.name;
    const seed = `${product.id}-${name}`;
    const features = (product.features || []).map((feature) => lowerFirst(clean(feature)));
    const featureText = features.length > 1
        ? `${features.slice(0, -1).join(', ')} and ${features[features.length - 1]}`
        : features[0] || 'the capabilities described above';
    const brand = clean(product.brand) || 'Neurostore';

    const intros = [
        `${name} is part of Neurostore's ${category.title} range. It covers ${featureText}, and is scoped to your environment rather than sold as a fixed package.`,
        `Organisations that need ${lowerFirst(clean(product.shortDescription).replace(/\.$/, ''))} can start with ${name}. Capabilities include ${featureText}.`,
        `${name}, delivered through ${brand}, brings together ${featureText}. Neurostore agrees the scope, deployment requirements and subscription options with you before anything is ordered.`,
    ];

    const faqs = [
        { q: `What is included in ${name}?`, a: `${name} includes ${featureText}. The exact scope is confirmed with you during consultation.` },
        { q: `How is ${name} priced?`, a: `${name} is quote-based and no price is shown online. Use the Request Quote or Call button and our team will confirm pricing for your environment.` },
        { q: `How is ${name} set up?`, a: 'Neurostore confirms the service scope, deployment requirements and delivery plan with you before work begins, then supports the service after deployment.' },
    ];

    const delivery = [
        row('Pricing', 'Price on request'),
        row('Delivery', info.Delivery),
        row('Service type', product.softwareType),
        row('Licence term', product.term),
        row('Support', info.Support),
        row('Product ID', info['Product ID'] || product.productId),
    ].filter(Boolean);

    return {
        categoryTitle: category.title,
        intro: pick(intros, seed),
        faqs,
        delivery,
        deliveryNote: `Scope, timelines and support for ${name} are confirmed with the final quotation.`,
    };
};

const hardwareContent = (product, category) => {
    const info = product.additionalInfo || {};
    const name = product.name;
    const specs = [info.CPU, info.Memory && `${info.Memory} memory`, info.Storage && `${info.Storage} storage`].filter(Boolean).join(', ');

    const delivery = [
        row('Pricing', 'Price on request'),
        row('Delivery', info.Delivery),
        row('Product type', info['Product Type']),
        row('Processor', info.CPU),
        row('Memory', info.Memory),
        row('Storage', info.Storage),
        row('Power input', info.Input),
        row('Supported OS', info['Supported OS']),
    ].filter(Boolean);

    return {
        categoryTitle: category.title,
        intro: `${name} is a compact AI workstation${specs ? ` built around ${specs}` : ''}. It is aimed at teams that want to run AI models, analyse data and handle content work locally without a separate GPU card.`,
        faqs: [
            { q: `What are the main specifications of ${name}?`, a: `${specs || 'See the Additional Information tab for the full specification'}. These are taken from the product listing; our team can confirm configuration options.` },
            { q: `How is ${name} priced?`, a: `${name} is quote-based. Use the Request Quote or Call button and our team will confirm price, availability and lead time.` },
            { q: 'What warranty comes with it?', a: 'Warranty terms are not listed for this product. Our team will confirm the manufacturer warranty before you order.' },
        ],
        delivery,
        deliveryNote: `${name} is a physical product shipped to you; delivery timing is confirmed in your quotation.`,
    };
};

export const buildProductContent = (product) => {
    const category = getCategory(product);
    if (product.brand === 'Adobe') return adobeContent(product, category);
    if (/^ai pc$/i.test(clean(product.brand))) return hardwareContent(product, category);
    if (product.enquiryOnly && !product.additionalInfo?.['Part Number']) return serviceContent(product, category);
    return microsoftContent(product, category);
};

/* ───────────────────────── Category page copy ───────────────────────── */

export const describeCategory = (entry) => {
    const families = new Set(entry.products.map((product) => product.family)).size;
    const priced = entry.products.filter((product) => !isQuoteOnly(product)).length;
    const countText = `${entry.products.length} ${entry.products.length === 1 ? 'product' : 'products'}`;
    const familyText = families > 1 ? ` across ${families} product families` : '';
    const priceText = priced === 0 ? 'Pricing is provided on request.'
        : priced === entry.products.length ? 'Prices are shown before 18% GST.'
            : `${priced} have listed prices (before 18% GST); the rest are quoted on request.`;
    return `${entry.category.blurb} This category lists ${countText}${familyText}. ${priceText}`;
};

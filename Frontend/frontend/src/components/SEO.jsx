import { Helmet } from 'react-helmet-async';
import { useLocation } from 'react-router-dom';

function SEO({ 
  title, 
  description, 
  keywords,
  ogImage = 'https://www.neurostore.in/og-image.webp',
  ogType = 'website'
}) {
  const location = useLocation();
  const canonicalUrl = `https://www.neurostore.in${location.pathname}`;

  return (
    <Helmet>
      {/* ── Basic SEO ── */}
      <title>{title}</title>
      <meta name="description" content={description} />
      {keywords && <meta name="keywords" content={keywords} />}
      <link rel="canonical" href={canonicalUrl} />

      {/* ── Open Graph ── */}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:type" content={ogType} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:site_name" content="Neurostore" />

      {/* ── Twitter Card ── */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
    </Helmet>
  );
}

export default SEO;
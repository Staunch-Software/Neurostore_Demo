import { Helmet } from 'react-helmet-async';
import { useLocation } from 'react-router-dom';

function SEO({ 
  title, 
  description, 
  keywords,
  ogImage = 'https://staunchtec.com/img/logo-img.webp', // your default share image
  ogType = 'website'
}) {
  const location = useLocation();
  const canonicalUrl = `https://www.neurostore.in${location.pathname}`;

  return (
    <Helmet>
      {/* ── Basic SEO ── */}
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <link rel="canonical" href={canonicalUrl} />

      {/* ── Open Graph (Facebook, WhatsApp, LinkedIn) ── */}
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

      {/* ── Google Analytics ── */}
      <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
      <script>
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-XXXXXXXXXX');
        `}
      </script>
    </Helmet>
  );
}

export default SEO;
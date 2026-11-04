   export function trackEvent(name, params = {}) {
     try {
       if (typeof window !== 'undefined' && typeof window.gtag === 'function') {
         window.gtag('event', name, params);
       }
     } catch (e) {
       // tracking must never break the site
     }
   }

   export function trackAdsConversion(sendTo, params = {}) {
     trackEvent('conversion', { send_to: sendTo, ...params });
   }
// Enquiry-only or unpriced products can be added to the cart but are quoted, not paid for online.
export const isQuoteOnly = (product) =>
    Boolean(product?.enquiryOnly) || !(Number(product?.price) > 0);

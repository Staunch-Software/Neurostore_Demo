import React, { useContext, useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowRight, ChevronRight } from 'lucide-react';
import SEO from '../components/SEO';
import { ShopContext } from '../components/context/ShopContext';
import { isQuoteOnly } from '../pricing';
import { CATEGORY_GROUPS, describeCategory, getCategoryIndex, getCategoryList, productSlug, slugify } from '../catalog';
import './Categories.css';

const groupByFamily = (list) => {
    const groups = [];
    list.forEach((product) => {
        const last = groups[groups.length - 1];
        if (last && last.family === product.family) last.products.push(product);
        else groups.push({ family: product.family, products: [product] });
    });
    return groups;
};

const priceLabel = (product) =>
    isQuoteOnly(product) ? 'Price on Request' : `₹${Number(product.price).toLocaleString('en-IN')} + GST`;

export const CategoryPage = () => {
    const { categorySlug } = useParams();
    const { products } = useContext(ShopContext);
    const index = useMemo(() => getCategoryIndex(products), [products]);
    const entry = index.get(categorySlug);
    const otherCategories = useMemo(
        () => getCategoryList(products).filter((item) => item.category.slug !== categorySlug && item.category.group === entry?.category.group),
        [products, categorySlug, entry],
    );

    if (!products || products.length === 0) {
        return <div className="cat-page"><div className="cat-container cat-state">Loading category...</div></div>;
    }

    if (!entry) {
        return (
            <>
                <SEO title="Category not found | Neurostore" description="This category is no longer available on Neurostore." noindex />
                <div className="cat-page">
                    <div className="cat-container cat-state">
                        Category not found. <Link to="/categories">Browse all categories</Link>
                    </div>
                </div>
            </>
        );
    }

    const { category } = entry;
    const families = groupByFamily(entry.products);
    const description = describeCategory(entry);

    return (
        <>
            <SEO
                title={`${category.title} - Buy Online in India | Neurostore`}
                description={description.slice(0, 300)}
                keywords={`${category.title}, buy ${category.title} India, ${category.group} licences India, neurostore`}
            />
            <div className="cat-page">
                <div className="cat-container">
                    <nav className="cat-breadcrumb" aria-label="Breadcrumb">
                        <Link to="/">Home</Link><ChevronRight size={14} />
                        <Link to="/categories">Categories</Link><ChevronRight size={14} />
                        <span>{category.title}</span>
                    </nav>

                    <header className="cat-header">
                        <span className="cat-group-badge">{category.group}</span>
                        <h1 className="cat-title">{category.title}</h1>
                        <p className="cat-description">{description}</p>
                    </header>

                    {families.length > 1 && (
                        <nav className="cat-family-nav" aria-label="Product families in this category">
                            {families.map((group) => (
                                <a key={group.family} href={`#family-${slugify(group.family)}`}>
                                    {group.family} <span>{group.products.length}</span>
                                </a>
                            ))}
                        </nav>
                    )}

                    {families.map((group) => (
                        <section className="cat-family" id={`family-${slugify(group.family)}`} key={group.family}>
                            <h2>{group.family}</h2>
                            <ul className="cat-product-list">
                                {group.products.map((product) => (
                                    <li key={product.id}>
                                        <Link to={`/products/${productSlug(product)}`} title={product.name}>
                                            <span className="cat-product-thumb">
                                                <img src={product.image} alt="" loading="lazy" />
                                            </span>
                                            <span className="cat-product-info">
                                                <span className="cat-product-name">{product.name}</span>
                                                <span className="cat-product-meta">
                                                    {product.term && <span className="cat-product-chip">{product.term}</span>}
                                                    <strong>{priceLabel(product)}</strong>
                                                </span>
                                            </span>
                                            <ArrowRight size={16} className="cat-product-arrow" />
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    ))}

                    {otherCategories.length > 0 && (
                        <section className="cat-more">
                            <h2>More {category.group} categories</h2>
                            <div className="cat-chip-row">
                                {otherCategories.map((item) => (
                                    <Link key={item.category.slug} to={`/category/${item.category.slug}`}>{item.category.title}</Link>
                                ))}
                                <Link to="/categories" className="cat-chip-all">All categories <ArrowRight size={14} /></Link>
                            </div>
                        </section>
                    )}
                </div>
            </div>
        </>
    );
};

export const CategoriesIndex = () => {
    const { products } = useContext(ShopContext);
    const list = useMemo(() => getCategoryList(products), [products]);

    return (
        <>
            <SEO
                title="Shop by Category - Software Licences, Security & AI Hardware | Neurostore"
                description="Browse Neurostore by category: Windows Server, CALs, SQL Server, Windows 10 ESU, Project Server, Adobe Acrobat and Creative Cloud, backup and cybersecurity services."
                keywords="software categories India, Windows Server CAL, SQL Server licence, Windows 10 ESU, Adobe Acrobat, Creative Cloud, neurostore"
            />
            <div className="cat-page">
                <div className="cat-container">
                    <nav className="cat-breadcrumb" aria-label="Breadcrumb">
                        <Link to="/">Home</Link><ChevronRight size={14} />
                        <span>Categories</span>
                    </nav>
                    <header className="cat-header">
                        <h1 className="cat-title">Shop by Category</h1>
                        <p className="cat-description">
                            Every product on Neurostore grouped by what it does, so you can compare variants such as
                            User and Device CALs or 1-year and 3-year terms in one place.
                        </p>
                    </header>

                    {list.length === 0 && <div className="cat-state">Loading categories...</div>}

                    {CATEGORY_GROUPS.map((group) => {
                        const items = list.filter((item) => item.category.group === group);
                        if (items.length === 0) return null;
                        return (
                            <section className="cat-family" key={group}>
                                <h2>{group}</h2>
                                <div className="cat-card-grid">
                                    {items.map((item) => (
                                        <Link className="cat-card" key={item.category.slug} to={`/category/${item.category.slug}`}>
                                            <strong>{item.category.title}</strong>
                                            <p>{item.category.blurb}</p>
                                            <span>{item.products.length} {item.products.length === 1 ? 'product' : 'products'} <ArrowRight size={14} /></span>
                                        </Link>
                                    ))}
                                </div>
                            </section>
                        );
                    })}
                </div>
            </div>
        </>
    );
};

export default CategoryPage;

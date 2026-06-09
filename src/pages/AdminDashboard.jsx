import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const AdminDashboard = () => {
    const navigate = useNavigate();
    const [products, setProducts] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    // Add Product Form State
    const [newProduct, setNewProduct] = useState({ name: '', category: '', price: '', shortDescription: '' });
    const [isAdding, setIsAdding] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('adminToken');
        if (!token) {
            navigate('/admin');
        } else {
            fetchProducts();
        }
    }, [navigate]);

    const fetchProducts = async () => {
        try {
            const res = await fetch('https://www.neurostore.in/api/products');
            const data = await res.json();
            setProducts(data);
            setIsLoading(false);
        } catch (err) {
            console.error("Error fetching products", err);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('adminToken');
        navigate('/admin');
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this product?")) return;

        try {
            const token = localStorage.getItem('adminToken');
            const res = await fetch(`https://www.neurostore.in/api/admin/product/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Basic ${token}` }
            });
            if (res.ok) {
                setProducts(products.filter(p => p.id !== id));
            }
        } catch (err) {
            alert("Error deleting product.");
        }
    };

    const handleAddProduct = async (e) => {
        e.preventDefault();
        setIsAdding(true);

        try {
            const token = localStorage.getItem('adminToken');
            const res = await fetch('https://www.neurostore.in/api/admin/product', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Basic ${token}` },
                body: JSON.stringify(newProduct)
            });

            if (res.ok) {
                alert("Product Added!");
                setNewProduct({ name: '', category: '', price: '', shortDescription: '' });
                fetchProducts(); // Refresh the list
            }
        } catch (err) {
            alert("Error adding product.");
        } finally {
            setIsAdding(false);
        }
    };

    if (isLoading) return <div style={{color: 'white', padding: '50px', background: '#0f172a', height: '100vh'}}>Loading Secure Terminal...</div>;

    return (
        <div style={{ padding: '60px 40px', background: '#0f172a', minHeight: '100vh', fontFamily: 'Inter', color: 'white' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px', borderBottom: '1px solid #1e293b', paddingBottom: '20px' }}>
                <div>
                    <h1 style={{ fontSize: '32px', margin: 0, color: '#38bdf8' }}>System Terminal</h1>
                    <p style={{ color: '#94a3b8', margin: '5px 0 0 0' }}>Admin Control Center</p>
                </div>
                <button onClick={handleLogout} style={{ background: '#ef4444', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
                    Secure Logout
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '30px' }}>

                {/* LEFT: INVENTORY TABLE */}
                <div style={{ background: '#1e293b', padding: '25px', borderRadius: '15px' }}>
                    <h2 style={{ marginTop: 0, marginBottom: '20px', fontSize: '20px' }}>Current Inventory ({products.length})</h2>
                    <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                            <thead>
                                <tr style={{ borderBottom: '2px solid #334155', color: '#94a3b8' }}>
                                    <th style={{ padding: '10px' }}>ID</th>
                                    <th style={{ padding: '10px' }}>Product Name</th>
                                    <th style={{ padding: '10px' }}>Price</th>
                                    <th style={{ padding: '10px' }}>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {products.map(p => (
                                    <tr key={p.id} style={{ borderBottom: '1px solid #334155' }}>
                                        <td style={{ padding: '12px 10px', color: '#cbd5e1' }}>#{p.id}</td>
                                        <td style={{ padding: '12px 10px', fontWeight: '500' }}>{p.name}</td>
                                        <td style={{ padding: '12px 10px', color: '#10b981' }}>₹{p.price.toLocaleString()}</td>
                                        <td style={{ padding: '12px 10px' }}>
                                            <button onClick={() => handleDelete(p.id)} style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: '1px solid #ef4444', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer' }}>
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* RIGHT: ADD PRODUCT FORM */}
                <div style={{ background: '#1e293b', padding: '25px', borderRadius: '15px', height: 'fit-content' }}>
                    <h2 style={{ marginTop: 0, marginBottom: '20px', fontSize: '20px', color: '#10b981' }}>+ Add Product</h2>
                    <form onSubmit={handleAddProduct} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                        <input type="text" placeholder="Product Name" required value={newProduct.name} onChange={e => setNewProduct({...newProduct, name: e.target.value})} style={{ padding: '10px', borderRadius: '6px', border: 'none', background: '#0f172a', color: 'white' }} />
                        <input type="text" placeholder="Category" required value={newProduct.category} onChange={e => setNewProduct({...newProduct, category: e.target.value})} style={{ padding: '10px', borderRadius: '6px', border: 'none', background: '#0f172a', color: 'white' }} />
                        <input type="number" placeholder="Price (₹)" required value={newProduct.price} onChange={e => setNewProduct({...newProduct, price: e.target.value})} style={{ padding: '10px', borderRadius: '6px', border: 'none', background: '#0f172a', color: 'white' }} />
                        <textarea placeholder="Short Description" required value={newProduct.shortDescription} onChange={e => setNewProduct({...newProduct, shortDescription: e.target.value})} rows="3" style={{ padding: '10px', borderRadius: '6px', border: 'none', background: '#0f172a', color: 'white', resize: 'none' }} />

                        <button type="submit" disabled={isAdding} style={{ background: '#10b981', color: 'white', border: 'none', padding: '12px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' }}>
                            {isAdding ? 'Adding...' : 'Push to Database'}
                        </button>
                    </form>
                </div>

            </div>
        </div>
    );
};

export default AdminDashboard;

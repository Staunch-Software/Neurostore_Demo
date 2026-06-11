import React, { useState } from "react";
import { Helmet } from 'react-helmet-async';
import '../pages/Brandcomponents.css';

// ✅ IMPORT IMAGES FROM src/assets
import amdLogo from "../assets/amd-logo.png";
import aocLogo from "../assets/AOC.webp";
import acerLogo from "../assets/acer-logo.png";
import asusLogo from "../assets/asus-logo-removebg-preview.png";
import arubaLogo from "../assets/aruba-logo.webp";
import crucialLogo from "../assets/crucial-logo.png";
import dellLogo from "../assets/dell-png-logo-3741.png";
import hpLogo from "../assets/hp-logo-2-removebg-preview.png";
import intelLogo from "../assets/intel-logo1.png";
import lenovoLogo from "../assets/lenovo-logo-removebg-preview.png";
import micronLogo from "../assets/Micron-Logo.png";
import philipsLogo from "../assets/Phillips-Logo.png";
import samsungLogo from "../assets/Samsung-logo-removebg-preview.png";
import seagateLogo from "../assets/seagate img.png";
import supermicroLogo from "../assets/supermicro-logo-removebg-preview.png";
import tinyLogo from "../assets/tiny-logo-removebg-preview.png";
import toshibaLogo from "../assets/toshiba-logo-icon.webp";
import westernDigitalLogo from "../assets/Western-Digital-Logo(2).png";


// Brand Data
const brands = [
  { name: "AMD", logo: amdLogo, initial: "A" },
  { name: "AOC", logo: aocLogo, initial: "A" },
  { name: "Acer", logo: acerLogo, initial: "A" },
  { name: "Asus", logo: asusLogo, initial: "A" },
  { name: "Aruba", logo: arubaLogo, initial: "A" },

  { name: "Crucial", logo: crucialLogo, initial: "C" },
  { name: "Dell", logo: dellLogo, initial: "D" },
  { name: "HP", logo: hpLogo, initial: "H" },
  { name: "Intel", logo: intelLogo, initial: "I" },
  { name: "Lenovo", logo: lenovoLogo, initial: "L" },
  { name: "Micron", logo: micronLogo, initial: "M" },
  { name: "Philips", logo: philipsLogo, initial: "P" },

  { name: "Samsung", logo: samsungLogo, initial: "S" },
  { name: "Supermicro", logo: supermicroLogo, initial: "S" },
  { name: "Seagate", logo: seagateLogo, initial: "S" },

  { name: "Toshiba", logo: toshibaLogo, initial: "T" },
  { name: "Tiny", logo: tinyLogo, initial: "T" },

  { name: "Western Digital", logo: westernDigitalLogo, initial: "W" },
];

const alphabet = ["ALL", ...Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i))];

export default function BrandSuppliers() {
  const [selectedLetter, setSelectedLetter] = useState("ALL");

  const filteredBrands =
    selectedLetter === "ALL"
      ? brands
      : brands.filter((brand) => brand.initial === selectedLetter);

  return (
    <>
          <Helmet>
          <link rel="canonical" href="https://www.neurostore.in/brands"/>
          </Helmet>
    <div className="brand-container">
      <header className="brand-header">
        <h1>Our Brand Suppliers</h1>
        <p>Select a letter to filter the available brands.</p>
      </header>

      <div className="brand-alphabet-filter-container">
        <div className="brand-alphabet-filter">
          {alphabet.map((letter) => (
            <button
              key={letter}
              className={`brand-filter-btn ${selectedLetter === letter ? "brand-active" : ""}`}
              onClick={() => setSelectedLetter(letter)}
            >
              {letter}
            </button>
          ))}
        </div>
      </div>

      <div className="brand-brands-grid">
        {filteredBrands.map((brand, index) => (
          <div 
            key={index} 
            className="brand-item"
            style={{ animationDelay: `${index * 0.05}s` }}
          >
            <div className="brand-card">
              <div className="brand-logo-wrapper">
                <img src={brand.logo} alt={`${brand.name} Logo`} />
              </div>
              <div className="brand-overlay">
                <span className="brand-name">{brand.name}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
    </>
  );
}
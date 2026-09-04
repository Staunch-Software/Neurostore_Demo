import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { ArrowUp } from "lucide-react";
import "../pages/floatingreachus.css";

export default function ScrollToTop() {
  const { pathname } = useLocation();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  useEffect(() => {
    const handleScroll = () => setIsVisible(window.scrollY > 300);

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  if (!isVisible) return null;

  return (
    <button
      type="button"
      className="scroll-to-top-btn"
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      aria-label="Scroll to top"
      title="Scroll to top"
    >
      <ArrowUp size={21} aria-hidden="true" />
    </button>
  );
}
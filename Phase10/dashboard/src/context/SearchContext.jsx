import { createContext, useContext, useState, useEffect, useCallback } from "react";

const SearchContext = createContext(null);

export function SearchProvider({ children }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");

  const openSearch = useCallback(() => { setIsOpen(true); setQuery(""); }, []);
  const closeSearch = useCallback(() => { setIsOpen(false); setQuery(""); }, []);

  // 글로벌 Ctrl+K / Cmd+K
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen(prev => !prev);
        if (!isOpen) setQuery("");
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen]);

  return (
    <SearchContext.Provider value={{ isOpen, query, setQuery, openSearch, closeSearch }}>
      {children}
    </SearchContext.Provider>
  );
}

export function useSearch() {
  const ctx = useContext(SearchContext);
  if (!ctx) throw new Error("useSearch must be used within SearchProvider");
  return ctx;
}

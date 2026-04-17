import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <a href="#home" className="logo" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="logo-icon">📄</div>
            <h2>DocQuery</h2>
          </a>
          <nav className="nav">
            <a href="#about" className="nav-link" onClick={(e) => {
              e.preventDefault();
              document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' });
            }}>About</a>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;

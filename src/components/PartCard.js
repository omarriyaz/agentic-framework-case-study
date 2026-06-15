import React from "react";
import "./PartCard.css";

function PartCard({ part, onAddToCart }) {
  const hasPrice =
    part.price && !String(part.price).toLowerCase().includes("see") && !isNaN(Number(part.price));

  return (
    <div className="part-card">
      <div className="part-card-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
        </svg>
      </div>
      <div className="part-card-body">
        <div className="part-card-name">{part.name}</div>
        <div className="part-card-meta">
          <span className="part-card-number">#{part.part_number}</span>
          {part.brand && <span className="part-card-brand">{part.brand}</span>}
          <span className={`part-card-category ${part.category?.toLowerCase()}`}>
            {part.category}
          </span>
        </div>
        <div className="part-card-price">
          {hasPrice ? (
            <span className="price-value">${Number(part.price).toFixed(2)}</span>
          ) : (
            <span className="price-check">
              <a href={part.url} target="_blank" rel="noreferrer">
                Check price →
              </a>
            </span>
          )}
        </div>
        {part.install && (
          <div className="part-card-install">
            <span className={`difficulty-badge difficulty-${part.install.difficulty?.toLowerCase().replace(" ", "-")}`}>
              {part.install.difficulty}
            </span>
            <span className="install-time">{part.install.time}</span>
          </div>
        )}
      </div>
      <div className="part-card-actions">
        <a
          className="btn-view"
          href={part.url}
          target="_blank"
          rel="noreferrer"
        >
          View
        </a>
        <button
          className="btn-cart"
          onClick={() => onAddToCart(part)}
        >
          Add to Cart
        </button>
      </div>
    </div>
  );
}

export default PartCard;

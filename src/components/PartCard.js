import React from "react";
import "./PartCard.css";

function StarRating({ rating, count }) {
  if (!rating) return null;
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <div className="part-card-rating">
      <span className="stars">
        {[1,2,3,4,5].map(i => (
          <svg key={i} className={`star ${i <= full ? "star-full" : i === full + 1 && half ? "star-half" : "star-empty"}`}
            viewBox="0 0 24 24" width="11" height="11">
            <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" />
          </svg>
        ))}
      </span>
      <span className="rating-value">{rating.toFixed(1)}</span>
      {count > 0 && <span className="rating-count">({count})</span>}
    </div>
  );
}

function PartCard({ part, onAddToCart }) {
  const hasPrice =
    part.price && !String(part.price).toLowerCase().includes("see") && !isNaN(Number(part.price));

  return (
    <div className="part-card">
      <div className="part-card-image-col">
        {part.image_url ? (
          <img
            className="part-card-img"
            src={part.image_url}
            alt={part.name}
            onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }}
          />
        ) : null}
        <div className="part-card-icon" style={part.image_url ? { display: "none" } : {}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
          </svg>
        </div>
      </div>

      <div className="part-card-body">
        <div className="part-card-name-row">
          <div className="part-card-name">{part.name}</div>
          {part.is_oem && <span className="oem-badge">OEM</span>}
        </div>

        <div className="part-card-meta">
          <span className="part-card-number">#{part.part_number}</span>
          {part.brand && <span className="part-card-brand">{part.brand}</span>}
          <span className={`part-card-category ${part.category?.toLowerCase()}`}>
            {part.category}
          </span>
        </div>

        <StarRating rating={part.rating} count={part.review_count} />

        <div className="part-card-price">
          {hasPrice ? (
            <span className="price-value">${Number(part.price).toFixed(2)}</span>
          ) : (
            <span className="price-check">
              <a href={part.url} target="_blank" rel="noreferrer">Check price →</a>
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
        <a className="btn-view" href={part.url} target="_blank" rel="noreferrer">View</a>
        <button className="btn-cart" onClick={() => onAddToCart(part)}>Add to Cart</button>
      </div>
    </div>
  );
}

export default PartCard;

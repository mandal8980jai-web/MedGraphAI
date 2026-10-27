import React from 'react';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Logo: React.FC<LogoProps> = ({ className = '', size = 'md' }) => {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
  }[size];

  return (
    <div className={`relative flex items-center justify-center shrink-0 ${sizeClasses} ${className}`}>
      <svg
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-full w-full drop-shadow-sm select-none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="headerShieldGrad" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0d9488" />
            <stop offset="50%" stopColor="#0891b2" />
            <stop offset="100%" stopColor="#0284c7" />
          </linearGradient>
          <linearGradient id="headerNodeGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#2dd4bf" />
          </linearGradient>
          <linearGradient id="headerCrossGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#e0f2fe" />
          </linearGradient>
          <filter id="headerShadow" x="-10%" y="-10%" width="120%" height="125%" filterUnits="userSpaceOnUse">
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="#0f172a" floodOpacity="0.2" />
          </filter>
        </defs>

        {/* Shield Geometry */}
        <path
          d="M24 4L7 11V22C7 32.5 14.3 42.1 24 44.5C33.7 42.1 41 32.5 41 22V11L24 4Z"
          fill="url(#headerShieldGrad)"
          filter="url(#headerShadow)"
        />

        {/* Subtle Shield Inner Highlight */}
        <path
          d="M24 6.5L9.5 12.5V22C9.5 31.2 15.8 39.8 24 42C32.2 39.8 38.5 31.2 38.5 22V12.5L24 6.5Z"
          stroke="rgba(255,255,255,0.25)"
          strokeWidth="1"
        />

        {/* Knowledge Graph Web Lines */}
        <g stroke="rgba(255, 255, 255, 0.45)" strokeWidth="1.5" strokeLinecap="round">
          <line x1="24" y1="15" x2="16" y2="21" />
          <line x1="24" y1="15" x2="32" y2="21" />
          <line x1="16" y1="21" x2="18" y2="31" />
          <line x1="32" y1="21" x2="30" y2="31" />
          <line x1="18" y1="31" x2="24" y2="34" />
          <line x1="30" y1="31" x2="24" y2="34" />
        </g>

        {/* Central Medical Cross */}
        <g>
          <rect x="21.5" y="18" width="5" height="12" rx="2" fill="url(#headerCrossGrad)" />
          <rect x="18" y="21.5" width="12" height="5" rx="2" fill="url(#headerCrossGrad)" />
        </g>

        {/* Knowledge Graph Nodes */}
        <circle cx="24" cy="15" r="2.8" fill="url(#headerNodeGrad)" stroke="#ffffff" strokeWidth="1.2" />
        <circle cx="16" cy="21" r="2.4" fill="url(#headerNodeGrad)" stroke="#ffffff" strokeWidth="1.2" />
        <circle cx="32" cy="21" r="2.4" fill="url(#headerNodeGrad)" stroke="#ffffff" strokeWidth="1.2" />
        <circle cx="18" cy="31" r="2.4" fill="url(#headerNodeGrad)" stroke="#ffffff" strokeWidth="1.2" />
        <circle cx="30" cy="31" r="2.4" fill="url(#headerNodeGrad)" stroke="#ffffff" strokeWidth="1.2" />
        <circle cx="24" cy="34" r="2.8" fill="url(#headerNodeGrad)" stroke="#ffffff" strokeWidth="1.2" />

        {/* Core Center Indicator */}
        <circle cx="24" cy="24" r="1.6" fill="#0284c7" />
      </svg>
    </div>
  );
};


import React from 'react';

interface GlukDebateLogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
}

export const GlukDebateLogo: React.FC<GlukDebateLogoProps> = ({
  className = '',
  size = 48,
  showText = false,
}) => {
  return (
    <div className={`inline-flex items-center gap-3 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 320 320"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0 drop-shadow-md select-none"
        aria-label="Great Lakes University of Kisumu Debate Club Crest"
      >
        <defs>
          {/* Circular paths for arched text */}
          <path
            id="textPathTop"
            d="M 40,160 A 120,120 0 0,1 280,160"
            fill="none"
          />
          <path
            id="textPathBottom"
            d="M 276,168 A 120,120 0 0,1 44,168"
            fill="none"
          />
          {/* Subtle gold gradient for metallic luster */}
          <linearGradient id="goldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f7dc8a" />
            <stop offset="45%" stopColor="#d8a135" />
            <stop offset="100%" stopColor="#b67f1b" />
          </linearGradient>
          {/* Deep collegiate navy background */}
          <radialGradient id="navyBg" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#132347" />
            <stop offset="100%" stopColor="#081022" />
          </radialGradient>
        </defs>

        {/* Outer Navy Circular Background */}
        <circle cx="160" cy="160" r="154" fill="url(#navyBg)" />

        {/* Outer Gold Ring Border */}
        <circle cx="160" cy="160" r="148" stroke="url(#goldGradient)" strokeWidth="6" />
        <circle cx="160" cy="160" r="140" stroke="url(#goldGradient)" strokeWidth="2.5" />

        {/* Middle Ring Border for Text Band */}
        <circle cx="160" cy="160" r="98" stroke="url(#goldGradient)" strokeWidth="3" />

        {/* Arched Typography - GREAT LAKES UNIVERSITY OF KISUMU */}
        <text
          fill="url(#goldGradient)"
          fontSize="14.8"
          fontWeight="800"
          fontFamily="sans-serif"
          letterSpacing="2.2"
        >
          <textPath href="#textPathTop" startOffset="50%" textAnchor="middle">
            GREAT LAKES UNIVERSITY OF KISUMU
          </textPath>
        </text>

        {/* Star Accents */}
        <path
          d="M 36,160 L 41,154 L 46,160 L 41,166 Z"
          fill="url(#goldGradient)"
        />
        <path
          d="M 274,160 L 279,154 L 284,160 L 279,166 Z"
          fill="url(#goldGradient)"
        />

        {/* Arched Typography - DEBATE CLUB */}
        <text
          fill="url(#goldGradient)"
          fontSize="17"
          fontWeight="800"
          fontFamily="sans-serif"
          letterSpacing="4"
        >
          <textPath href="#textPathBottom" startOffset="50%" textAnchor="middle">
            DEBATE CLUB
          </textPath>
        </text>

        {/* Inner Laurel Wreath Left & Right */}
        <g stroke="url(#goldGradient)" fill="url(#goldGradient)">
          {/* Laurel branch curves */}
          <path
            d="M 100,205 C 80,185 80,135 102,112"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
          />
          <path
            d="M 220,205 C 240,185 240,135 218,112"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
          />

          {/* Laurel leaves left */}
          <ellipse cx="88" cy="192" rx="7" ry="3.5" transform="rotate(-30 88 192)" />
          <ellipse cx="82" cy="174" rx="7.5" ry="3.5" transform="rotate(-15 82 174)" />
          <ellipse cx="81" cy="154" rx="7.5" ry="3.5" transform="rotate(5 81 154)" />
          <ellipse cx="85" cy="135" rx="7.5" ry="3.5" transform="rotate(25 85 135)" />
          <ellipse cx="94" cy="119" rx="6.5" ry="3.5" transform="rotate(45 94 119)" />

          <ellipse cx="98" cy="182" rx="6.5" ry="3" transform="rotate(25 98 182)" />
          <ellipse cx="94" cy="163" rx="6.5" ry="3" transform="rotate(35 94 163)" />
          <ellipse cx="95" cy="144" rx="6.5" ry="3" transform="rotate(45 95 144)" />
          <ellipse cx="102" cy="128" rx="6" ry="3" transform="rotate(60 102 128)" />

          {/* Laurel leaves right */}
          <ellipse cx="232" cy="192" rx="7" ry="3.5" transform="rotate(30 232 192)" />
          <ellipse cx="238" cy="174" rx="7.5" ry="3.5" transform="rotate(15 238 174)" />
          <ellipse cx="239" cy="154" rx="7.5" ry="3.5" transform="rotate(-5 239 154)" />
          <ellipse cx="235" cy="135" rx="7.5" ry="3.5" transform="rotate(-25 235 135)" />
          <ellipse cx="226" cy="119" rx="6.5" ry="3.5" transform="rotate(-45 226 119)" />

          <ellipse cx="222" cy="182" rx="6.5" ry="3" transform="rotate(-25 222 182)" />
          <ellipse cx="226" cy="163" rx="6.5" ry="3" transform="rotate(-35 226 163)" />
          <ellipse cx="225" cy="144" rx="6.5" ry="3" transform="rotate(-45 225 144)" />
          <ellipse cx="218" cy="128" rx="6" ry="3" transform="rotate(-60 218 128)" />
        </g>

        {/* Vintage Broadcast Microphone in Center */}
        {/* Outer U-fork bracket */}
        <path
          d="M 132,154 C 132,176 188,176 188,154"
          stroke="url(#goldGradient)"
          strokeWidth="4"
          fill="none"
          strokeLinecap="round"
        />
        {/* Stand stem & circular base */}
        <line x1="160" y1="172" x2="160" y2="198" stroke="url(#goldGradient)" strokeWidth="4.5" strokeLinecap="round" />
        <path d="M 144,198 L 176,198" stroke="url(#goldGradient)" strokeWidth="4" strokeLinecap="round" />

        {/* Microphone capsule body */}
        <rect
          x="142"
          y="120"
          width="36"
          height="46"
          rx="18"
          stroke="url(#goldGradient)"
          strokeWidth="3.5"
          fill="#0c172e"
        />
        {/* Horizontal microphone ribs */}
        <line x1="145" y1="131" x2="175" y2="131" stroke="url(#goldGradient)" strokeWidth="2.5" />
        <line x1="143" y1="137" x2="177" y2="137" stroke="url(#goldGradient)" strokeWidth="2.5" />
        <line x1="143" y1="143" x2="177" y2="143" stroke="url(#goldGradient)" strokeWidth="2.5" />
        <line x1="143" y1="149" x2="177" y2="149" stroke="url(#goldGradient)" strokeWidth="2.5" />
        <line x1="145" y1="155" x2="175" y2="155" stroke="url(#goldGradient)" strokeWidth="2.5" />
      </svg>

      {showText && (
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-tight text-white uppercase leading-tight font-serif">
            GLUK Debate Club
          </span>
          <span className="text-[11px] font-medium text-amber-400/90 tracking-wider">
            Great Lakes University of Kisumu
          </span>
        </div>
      )}
    </div>
  );
};



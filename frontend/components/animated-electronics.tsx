'use client'

import type { ReactNode } from 'react'

interface ElectronicSymbol {
  id: string
  type: 'resistor' | 'capacitor' | 'transistor' | 'diode' | 'inductor' | 'ic-chip' | 'circuit-board'
  svg: ReactNode
}

const ELECTRONICS_SYMBOLS = [
  {
    type: 'resistor',
    svg: (
      <svg width="60" height="30" viewBox="0 0 60 30" fill="none" stroke="white" strokeWidth="1.5">
        <line x1="0" y1="15" x2="10" y2="15" />
        <path d="M 10 15 L 12 10 L 14 20 L 16 10 L 18 20 L 20 10 L 22 15" />
        <line x1="22" y1="15" x2="60" y2="15" />
      </svg>
    ),
  },
  {
    type: 'capacitor',
    svg: (
      <svg width="50" height="35" viewBox="0 0 50 35" fill="none" stroke="white" strokeWidth="1.5">
        <line x1="0" y1="17" x2="18" y2="17" />
        <line x1="20" y1="8" x2="20" y2="26" />
        <line x1="30" y1="8" x2="30" y2="26" />
        <line x1="32" y1="17" x2="50" y2="17" />
      </svg>
    ),
  },
  {
    type: 'transistor',
    svg: (
      <svg width="45" height="50" viewBox="0 0 45 50" fill="none" stroke="white" strokeWidth="1.5">
        <circle cx="22" cy="25" r="12" />
        <line x1="0" y1="25" x2="10" y2="25" />
        <line x1="22" y1="13" x2="22" y2="0" />
        <line x1="22" y1="37" x2="22" y2="50" />
        <line x1="34" y1="25" x2="45" y2="25" />
      </svg>
    ),
  },
  {
    type: 'diode',
    svg: (
      <svg width="55" height="25" viewBox="0 0 55 25" fill="none" stroke="white" strokeWidth="1.5">
        <line x1="0" y1="12" x2="15" y2="12" />
        <polygon points="15,5 15,19 27,12" fill="white" opacity="0.3" />
        <line x1="27" y1="5" x2="27" y2="19" />
        <line x1="27" y1="12" x2="55" y2="12" />
      </svg>
    ),
  },
  {
    type: 'inductor',
    svg: (
      <svg width="55" height="30" viewBox="0 0 55 30" fill="none" stroke="white" strokeWidth="1.5">
        <line x1="0" y1="15" x2="5" y2="15" />
        <path d="M 5 15 Q 8 8 11 15 Q 14 22 17 15 Q 20 8 23 15" />
        <line x1="23" y1="15" x2="55" y2="15" />
      </svg>
    ),
  },
  {
    type: 'ic-chip',
    svg: (
      <svg width="50" height="50" viewBox="0 0 50 50" fill="none" stroke="white" strokeWidth="1">
        <rect x="8" y="8" width="34" height="34" />
        <circle cx="25" cy="25" r="6" />
        <circle cx="15" cy="15" r="2" />
        <circle cx="35" cy="15" r="2" />
        <circle cx="15" cy="35" r="2" />
        <circle cx="35" cy="35" r="2" />
      </svg>
    ),
  },
  {
    type: 'circuit-board',
    svg: (
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="white" strokeWidth="1">
        <circle cx="10" cy="10" r="3" fill="white" />
        <circle cx="30" cy="10" r="3" fill="white" />
        <circle cx="10" cy="30" r="3" fill="white" />
        <circle cx="30" cy="30" r="3" fill="white" />
        <line x1="10" y1="10" x2="30" y2="10" />
        <line x1="10" y1="10" x2="10" y2="30" />
        <line x1="30" y1="10" x2="30" y2="30" />
        <line x1="10" y1="30" x2="30" y2="30" />
      </svg>
    ),
  },
]

const POSITIONS = ['5%', '10%', '15%', '20%', '25%', '30%', '40%', '45%', '50%', '55%', '60%', '70%', '75%', '80%', '85%', '90%']

function getStablePosition(index: number) {
  const positionIndex = (index * 7) % POSITIONS.length
  const useLeft = index % 2 === 0

  return {
    [useLeft ? 'left' : 'right']: POSITIONS[positionIndex],
  }
}

export function AnimatedElectronics() {
  const elements = Array.from({ length: 30 }, (_, i) => ({
    id: `electronics-${i}`,
    symbol: ELECTRONICS_SYMBOLS[i % ELECTRONICS_SYMBOLS.length],
    delay: (i * 0.25) % 8,
    position: getStablePosition(i),
  }))

  return (
    <>
      <style>{`
        @keyframes slideUpFade {
          0% {
            opacity: 0;
            transform: translateY(100px);
          }
          10% {
            opacity: 0.6;
          }
          90% {
            opacity: 0.6;
          }
          100% {
            opacity: 0;
            transform: translateY(-100vh);
          }
        }

        .electronics-animate {
          animation: slideUpFade 8s ease-in infinite;
          position: absolute;
          opacity: 0.15;
        }
      `}</style>

      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {elements.map((el) => (
          <div
            key={el.id}
            className="electronics-animate"
            style={{
              ...el.position,
              animationDelay: `${el.delay}s`,
              top: '0',
            }}
          >
            {el.symbol.svg}
          </div>
        ))}
      </div>
    </>
  )
}

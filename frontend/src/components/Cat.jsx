// The Doc2All cat. Drawn from docs/design/doc2all-cat.html.
// It follows the pointer with its eyes and shows a heart when pressed.
import { useEffect, useId, useRef, useState } from 'react'

const clamp = (v) => Math.max(-1, Math.min(1, v))

export default function Cat({ mood = 'hello' }) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, '')
  const ref = useRef(null)
  const [boop, setBoop] = useState(0)

  useEffect(() => {
    const follow = (event) => {
      const svg = ref.current
      if (!svg) return
      const box = svg.getBoundingClientRect()
      svg.style.setProperty('--px', (clamp((event.clientX - box.left - box.width * 0.5) / (box.width * 0.8)) * 8).toFixed(1))
      svg.style.setProperty('--py', (clamp((event.clientY - box.top - box.height * 0.45) / (box.height * 0.8)) * 7).toFixed(1))
    }
    window.addEventListener('pointermove', follow)
    return () => window.removeEventListener('pointermove', follow)
  }, [])

  useEffect(() => {
    if (!boop) return undefined
    const timer = setTimeout(() => setBoop(0), 1000)
    return () => clearTimeout(timer)
  }, [boop])

  return (
    <svg ref={ref} className={boop ? 'cat boop' : 'cat'} viewBox="0 0 400 420" data-mood={mood} aria-hidden="true" onClick={() => setBoop(boop + 1)}>
      <defs>
      <clipPath id={`docClip${id}`}><rect x="-30" y="-40" width="60" height="76" rx="8"/></clipPath>
      <clipPath id={`eyeClipL${id}`}><ellipse cx="158" cy="186" rx="25" ry="29"/></clipPath>
      <clipPath id={`eyeClipR${id}`}><ellipse cx="242" cy="186" rx="25" ry="29"/></clipPath>
      <linearGradient id={`beamGrad${id}`} x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stopColor="#19B5D6" stopOpacity="0"/>
      <stop offset="1" stopColor="#19B5D6" stopOpacity=".7"/>
      </linearGradient>
      </defs>
      <ellipse className="shadow" cx="200" cy="402" rx="118" ry="13"/>
      <g className="boop-g"><g className="cat-all">
      {/* tail */}
      <g className="tail">
      <path className="line s-ginger" strokeWidth="30" d="M282 352 C352 362 376 292 342 250"/>
      <path className="line s-dark" strokeWidth="30" d="M350 272 C346 264 343 258 341 251"/>
      </g>
      {/* body */}
      <g className="body-g">
      <ellipse className="f-ginger" cx="200" cy="322" rx="90" ry="76"/>
      <ellipse className="f-dark" cx="124" cy="352" rx="36" ry="30"/>
      <ellipse className="f-dark" cx="276" cy="352" rx="36" ry="30"/>
      <ellipse className="f-cream" cx="200" cy="338" rx="50" ry="56"/>
      </g>
      {/* document held in front */}
      <g className="doc" transform="translate(200 354)">
      <rect className="f-white" x="-30" y="-40" width="60" height="76" rx="8" stroke="var(--docline)" strokeWidth="3"/>
      <rect className="doc-head" x="-30" y="-40" width="60" height="14" clipPath={`url(#docClip${id})`}/>
      <g fill="var(--docline)">
      <rect x="-20" y="-18" width="40" height="5" rx="2.5"/>
      <rect x="-20" y="-6" width="32" height="5" rx="2.5"/>
      <rect x="-20" y="6" width="40" height="5" rx="2.5"/>
      <rect x="-20" y="18" width="24" height="5" rx="2.5"/>
      </g>
      <g clipPath={`url(#docClip${id})`} className="beam"><g className="beam-g">
      <rect x="-30" y="-22" width="60" height="22" fill={`url(#beamGrad${id})`}/>
      <rect x="-30" y="-1.5" width="60" height="3" fill="var(--scan)"/>
      </g></g>
      <g className="badge-safe" transform="translate(28 -38)">
      <circle r="15" fill="var(--safe)" stroke="#fff" strokeWidth="3"/>
      <path className="line" stroke="#fff" strokeWidth="4" d="M-6 0 L-2 5 L7 -5"/>
      </g>
      <g className="badge-alert" transform="translate(28 -38)">
      <circle r="15" fill="var(--warn)" stroke="#fff" strokeWidth="3"/>
      <path className="line" stroke="#fff" strokeWidth="4" d="M0 -7 V2"/>
      <circle cy="8" r="2.4" fill="#fff"/>
      </g>
      </g>
      {/* front paws */}
      <g className="paws">
      <rect className="f-ginger" x="136" y="340" width="38" height="52" rx="19"/>
      <rect className="f-ginger" x="226" y="340" width="38" height="52" rx="19"/>
      <ellipse className="f-cream" cx="155" cy="388" rx="21" ry="13"/>
      <ellipse className="f-cream" cx="245" cy="388" rx="21" ry="13"/>
      <path className="line s-dark" strokeWidth="3" d="M149 384 v7 M161 384 v7 M239 384 v7 M251 384 v7"/>
      </g>
      {/* head */}
      <g className="head-g">
      <g className="ear-l">
      <path className="f-ginger" d="M100 152 Q84 80 94 62 Q102 54 114 62 L174 110 Z"/>
      <path className="f-pink" d="M112 130 Q104 90 108 78 L152 110 Z"/>
      </g>
      <g className="ear-r">
      <path className="f-ginger" d="M300 152 Q316 80 306 62 Q298 54 286 62 L226 110 Z"/>
      <path className="f-pink" d="M288 130 Q296 90 292 78 L248 110 Z"/>
      </g>
      <ellipse className="f-ginger" cx="200" cy="196" rx="112" ry="92"/>
      <ellipse className="f-ginger" cx="98" cy="228" rx="22" ry="16"/>
      <ellipse className="f-ginger" cx="302" cy="228" rx="22" ry="16"/>
      <path className="line s-dark" strokeWidth="7" d="M200 108 v22 M178 112 l4 18 M222 112 l-4 18"/>
      <ellipse className="f-cream" cx="200" cy="238" rx="50" ry="36"/>
      <ellipse className="f-pink" cx="128" cy="226" rx="15" ry="9" opacity=".55"/>
      <ellipse className="f-pink" cx="272" cy="226" rx="15" ry="9" opacity=".55"/>
      {/* eyes, open */}
      <g className="open-eyes">
      <g className="eye-l" clipPath={`url(#eyeClipL${id})`}>
      <ellipse className="f-white" cx="158" cy="186" rx="25" ry="29"/>
      <g className="pupil"><g className="look">
      <circle className="f-ink core" cx="158" cy="188" r="15"/>
      <circle className="f-white" cx="153" cy="181" r="5"/><circle className="f-white" cx="165" cy="196" r="2.6"/>
      </g></g>
      </g>
      <g className="eye-r" clipPath={`url(#eyeClipR${id})`}>
      <ellipse className="f-white" cx="242" cy="186" rx="25" ry="29"/>
      <g className="pupil"><g className="look">
      <circle className="f-ink core" cx="242" cy="188" r="15"/>
      <circle className="f-white" cx="237" cy="181" r="5"/><circle className="f-white" cx="249" cy="196" r="2.6"/>
      </g></g>
      </g>
      </g>
      {/* eyes, happy */}
      <g className="happy-eyes">
      <path className="line s-ink" strokeWidth="8" d="M134 198 Q158 164 182 198"/>
      <path className="line s-ink" strokeWidth="8" d="M218 198 Q242 164 266 198"/>
      </g>
      {/* brows */}
      <g className="brows">
      <path className="line s-ink" strokeWidth="6" d="M130 154 Q158 144 186 154"/>
      <path className="line s-ink" strokeWidth="6" d="M214 154 Q242 144 270 154"/>
      </g>
      <path className="f-pink" d="M187 216 Q200 208 213 216 Q207 229 200 231 Q193 229 187 216 Z"/>
      <g className="m-idle line s-ink" strokeWidth="4">
      <path d="M200 231 V238"/><path d="M200 238 Q190 250 177 242"/><path d="M200 238 Q210 250 223 242"/>
      </g>
      <g className="m-safe">
      <path className="f-ink" style={{ fill: 'var(--mouth)' }} d="M178 240 Q200 280 222 240 Q200 248 178 240 Z"/>
      <ellipse className="f-pink" cx="200" cy="261" rx="10" ry="6"/>
      </g>
      <g className="m-alert">
      <ellipse style={{ fill: 'var(--mouth)' }} cx="200" cy="248" rx="8" ry="11"/>
      </g>
      <g className="whiskers line" stroke="var(--whisker)" strokeWidth="3">
      <path d="M150 238 L86 224 M150 246 L82 248 M152 254 L94 272"/>
      <path d="M250 238 L314 224 M250 246 L318 248 M248 254 L306 272"/>
      </g>
      </g>
      {/* effects */}
      <g className="sparks" fill="var(--gold)">
      <path className="spark" transform="translate(66 110) scale(1)" d="M0 -12 Q2 -2 12 0 Q2 2 0 12 Q-2 2 -12 0 Q-2 -2 0 -12Z"/>
      <path className="spark" transform="translate(338 92) scale(1.2)" d="M0 -12 Q2 -2 12 0 Q2 2 0 12 Q-2 2 -12 0 Q-2 -2 0 -12Z"/>
      <path className="spark" transform="translate(352 196) scale(.8)" d="M0 -12 Q2 -2 12 0 Q2 2 0 12 Q-2 2 -12 0 Q-2 -2 0 -12Z"/>
      <path className="spark" transform="translate(48 206) scale(.9)" d="M0 -12 Q2 -2 12 0 Q2 2 0 12 Q-2 2 -12 0 Q-2 -2 0 -12Z"/>
      </g>
      <g className="alerts" fill="var(--warn)">
      <g transform="translate(60 96) rotate(-18)"><rect x="-4" y="-16" width="8" height="20" rx="4"/><circle cy="12" r="4"/></g>
      <g transform="translate(340 96) rotate(18)"><rect x="-4" y="-16" width="8" height="20" rx="4"/><circle cy="12" r="4"/></g>
      </g>
      <path className="heart" transform="translate(200 56) scale(1.5)" fill="#FF6B8B" d="M0 8 C-14 -2 -12 -16 0 -9 C12 -16 14 -2 0 8Z"/>
      </g></g>
    </svg>
  )
}

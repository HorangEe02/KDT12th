import React, { useState, useEffect, useRef, useCallback } from 'react';

const MAP = [
  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
  [1,0,1,1,0,0,0,2,0,0,1,1,0,0,0,1],
  [1,0,1,0,0,0,0,0,0,0,0,1,0,3,0,1],
  [1,0,0,0,0,1,1,0,1,1,0,0,0,0,0,1],
  [1,0,0,2,0,1,0,0,0,1,0,0,0,0,0,1],
  [1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1],
  [1,0,1,0,0,0,3,0,0,0,0,0,1,0,0,1],
  [1,0,1,1,0,0,0,0,0,0,0,0,0,0,2,1],
  [1,0,0,0,0,0,0,0,1,1,1,0,0,0,0,1],
  [1,0,0,0,1,1,0,0,1,0,0,0,0,1,0,1],
  [1,0,2,0,1,0,0,0,0,0,3,0,0,1,0,1],
  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
  [1,0,0,1,1,0,0,2,0,0,1,1,0,0,0,1],
  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
];

const MAP_W = 16, MAP_H = 16;

export default function SimpsonsDoom() {
  const canvasRef = useRef(null);
  const keysRef = useRef({});
  const gameRef = useRef(null);
  const [screen, setScreen] = useState('menu');
  const [score, setScore] = useState({ donuts: 0, total: 0 });

  const initGame = useCallback(() => {
    const sprites = [];
    let total = 0;
    for (let y = 0; y < MAP_H; y++) {
      for (let x = 0; x < MAP_W; x++) {
        if (MAP[y][x] === 2) {
          sprites.push({ x: x + 0.5, y: y + 0.5, type: 'donut', active: true });
          total++;
        } else if (MAP[y][x] === 3) {
          sprites.push({ x: x + 0.5, y: y + 0.5, type: 'flanders', active: true, speed: 0.015 + Math.random() * 0.01 });
        }
      }
    }
    gameRef.current = {
      px: 1.5, py: 1.5, pa: 0,
      health: 100, donuts: 0, total,
      sprites, running: true
    };
    setScore({ donuts: 0, total });
    setScreen('playing');
  }, []);

  useEffect(() => {
    const kd = (e) => { keysRef.current[e.key.toLowerCase()] = true; keysRef.current[e.code] = true; };
    const ku = (e) => { keysRef.current[e.key.toLowerCase()] = false; keysRef.current[e.code] = false; };
    window.addEventListener('keydown', kd);
    window.addEventListener('keyup', ku);
    return () => { window.removeEventListener('keydown', kd); window.removeEventListener('keyup', ku); };
  }, []);

  useEffect(() => {
    if (screen !== 'playing') return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height, HH = H / 2;
    const FOV = Math.PI / 3, HFOV = FOV / 2, RAYS = 120, DA = FOV / RAYS, SC = W / RAYS;
    let animId;

    const loop = () => {
      const g = gameRef.current;
      if (!g || !g.running) return;

      const keys = keysRef.current;
      const cos = Math.cos(g.pa), sin = Math.sin(g.pa);
      let dx = 0, dy = 0;
      if (keys['w'] || keys['arrowup']) { dx += cos * 0.045; dy += sin * 0.045; }
      if (keys['s'] || keys['arrowdown']) { dx -= cos * 0.045; dy -= sin * 0.045; }
      if (keys['a']) { dx += sin * 0.04; dy -= cos * 0.04; }
      if (keys['d']) { dx -= sin * 0.04; dy += cos * 0.04; }
      if (keys['arrowleft']) g.pa -= 0.04;
      if (keys['arrowright']) g.pa += 0.04;

      if (MAP[Math.floor(g.py)][Math.floor(g.px + dx)] !== 1) g.px += dx;
      if (MAP[Math.floor(g.py + dy)][Math.floor(g.px)] !== 1) g.py += dy;

      g.sprites.forEach(s => {
        if (!s.active) return;
        if (s.type === 'flanders') {
          const ddx = g.px - s.x, ddy = g.py - s.y;
          const dist = Math.sqrt(ddx * ddx + ddy * ddy);
          if (dist > 0.4) {
            const nx = s.x + (ddx / dist) * s.speed;
            const ny = s.y + (ddy / dist) * s.speed;
            if (MAP[Math.floor(ny)][Math.floor(nx)] !== 1) { s.x = nx; s.y = ny; }
          }
          if (dist < 0.5) {
            g.health -= 0.4;
            if (g.health <= 0) { g.running = false; setScreen('gameover'); }
          }
        } else if (s.type === 'donut') {
          const ddx = g.px - s.x, ddy = g.py - s.y;
          if (Math.sqrt(ddx * ddx + ddy * ddy) < 0.5) {
            s.active = false;
            g.donuts++;
            g.health = Math.min(100, g.health + 15);
            setScore({ donuts: g.donuts, total: g.total });
            if (g.donuts >= g.total) { g.running = false; setScreen('victory'); }
          }
        }
      });

      // Sky gradient
      const skyGrad = ctx.createLinearGradient(0, 0, 0, HH);
      skyGrad.addColorStop(0, '#1e3a5f');
      skyGrad.addColorStop(1, '#87CEEB');
      ctx.fillStyle = skyGrad;
      ctx.fillRect(0, 0, W, HH);
      
      // Floor gradient
      const floorGrad = ctx.createLinearGradient(0, HH, 0, H);
      floorGrad.addColorStop(0, '#654321');
      floorGrad.addColorStop(1, '#3d2817');
      ctx.fillStyle = floorGrad;
      ctx.fillRect(0, HH, W, HH);

      // Raycasting
      const zbuf = [];
      let rayA = g.pa - HFOV;
      for (let i = 0; i < RAYS; i++) {
        const sinA = Math.sin(rayA), cosA = Math.cos(rayA);
        let depth = 0, hit = false, hitV = false;
        for (let d = 0; d < 1600 && !hit; d++) {
          const tx = g.px + d * cosA * 0.01;
          const ty = g.py + d * sinA * 0.01;
          const mx = Math.floor(tx), my = Math.floor(ty);
          if (mx >= 0 && mx < MAP_W && my >= 0 && my < MAP_H && MAP[my][mx] === 1) {
            depth = d * 0.01;
            hitV = Math.abs(tx - mx - 0.5) > Math.abs(ty - my - 0.5);
            hit = true;
          }
        }
        if (!hit) depth = 16;
        zbuf[i] = depth;
        
        const corrDepth = depth * Math.cos(g.pa - rayA);
        const wallH = Math.min(H / (corrDepth + 0.001), H * 2);
        let shade = Math.max(50, 220 - corrDepth * 12);
        if (hitV) shade *= 0.75;
        
        // Brick-like wall color
        const r = Math.min(255, shade + 50);
        const gr = Math.min(255, shade - 10);
        const b = Math.min(255, shade - 30);
        ctx.fillStyle = `rgb(${r},${gr},${b})`;
        ctx.fillRect(i * SC, HH - wallH / 2, SC + 1, wallH);
        rayA += DA;
      }

      // Sprites
      const spriteData = g.sprites
        .filter(s => s.active)
        .map(s => {
          const dx = s.x - g.px, dy = s.y - g.py;
          const dist = Math.sqrt(dx * dx + dy * dy);
          let angle = Math.atan2(dy, dx) - g.pa;
          while (angle > Math.PI) angle -= 2 * Math.PI;
          while (angle < -Math.PI) angle += 2 * Math.PI;
          return { s, dist, angle };
        })
        .filter(sp => Math.abs(sp.angle) < HFOV + 0.5)
        .sort((a, b) => b.dist - a.dist);

      spriteData.forEach(({ s, dist, angle }) => {
        const screenX = (angle / FOV + 0.5) * W;
        const rayIdx = Math.floor((angle / FOV + 0.5) * RAYS);
        if (rayIdx >= 0 && rayIdx < RAYS && zbuf[rayIdx] < dist) return;
        
        const scale = Math.min(2, 0.6 / (dist + 0.001));
        const sprH = H * scale;
        const sprW = sprH * 0.8;
        
        ctx.globalAlpha = Math.max(0.4, 1 - dist / 12);
        
        if (s.type === 'donut') {
          // Pink donut
          ctx.fillStyle = '#FF69B4';
          ctx.beginPath();
          ctx.ellipse(screenX, HH, sprW / 2, sprH / 2.5, 0, 0, Math.PI * 2);
          ctx.fill();
          // Hole
          ctx.fillStyle = '#8B4513';
          ctx.beginPath();
          ctx.arc(screenX, HH, sprW / 6, 0, Math.PI * 2);
          ctx.fill();
          // Sprinkles
          const colors = ['#FFD700', '#00FF00', '#00BFFF', '#FF4500'];
          for (let i = 0; i < 8; i++) {
            const a = (i / 8) * Math.PI * 2;
            const r = sprW / 3;
            ctx.fillStyle = colors[i % 4];
            ctx.fillRect(screenX + Math.cos(a) * r - 2, HH + Math.sin(a) * r * 0.6 - 1, 4, 3);
          }
        } else {
          // Flanders - body
          ctx.fillStyle = '#228B22';
          ctx.fillRect(screenX - sprW / 4, HH - sprH / 8, sprW / 2, sprH / 2);
          // Head
          ctx.fillStyle = '#FFD700';
          ctx.beginPath();
          ctx.arc(screenX, HH - sprH / 4, sprW / 4, 0, Math.PI * 2);
          ctx.fill();
          // Mustache
          ctx.fillStyle = '#8B4513';
          ctx.fillRect(screenX - sprW / 8, HH - sprH / 5, sprW / 4, sprH / 20);
          // Eyes
          ctx.fillStyle = 'white';
          ctx.beginPath();
          ctx.arc(screenX - sprW / 10, HH - sprH / 3.5, sprW / 12, 0, Math.PI * 2);
          ctx.arc(screenX + sprW / 10, HH - sprH / 3.5, sprW / 12, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = 'black';
          ctx.beginPath();
          ctx.arc(screenX - sprW / 10, HH - sprH / 3.5, sprW / 25, 0, Math.PI * 2);
          ctx.arc(screenX + sprW / 10, HH - sprH / 3.5, sprW / 25, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.globalAlpha = 1;
      });

      // HUD Background
      ctx.fillStyle = 'rgba(0,0,0,0.7)';
      ctx.fillRect(0, H - 50, W, 50);
      
      // Health bar
      ctx.fillStyle = '#333';
      ctx.fillRect(15, H - 38, 130, 24);
      const hpW = (g.health / 100) * 126;
      const hpColor = g.health > 50 ? '#00FF00' : g.health > 25 ? '#FFFF00' : '#FF0000';
      ctx.fillStyle = hpColor;
      ctx.fillRect(17, H - 36, hpW, 20);
      ctx.strokeStyle = '#FFD700';
      ctx.lineWidth = 2;
      ctx.strokeRect(15, H - 38, 130, 24);
      ctx.fillStyle = 'white';
      ctx.font = 'bold 14px Arial';
      ctx.fillText(`❤️ ${Math.floor(g.health)}`, 22, H - 20);

      // Donut counter
      ctx.fillStyle = '#FFD700';
      ctx.font = 'bold 22px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(`🍩 ${g.donuts} / ${g.total}`, W / 2, H - 18);
      ctx.textAlign = 'left';

      // Minimap
      const mapS = 80, cellS = mapS / MAP_W;
      const oX = W - mapS - 10, oY = 10;
      ctx.fillStyle = 'rgba(0,0,0,0.7)';
      ctx.fillRect(oX - 2, oY - 2, mapS + 4, mapS + 4);
      for (let my = 0; my < MAP_H; my++) {
        for (let mx = 0; mx < MAP_W; mx++) {
          ctx.fillStyle = MAP[my][mx] === 1 ? '#888' : '#333';
          ctx.fillRect(oX + mx * cellS, oY + my * cellS, cellS - 0.3, cellS - 0.3);
        }
      }
      g.sprites.forEach(sp => {
        if (sp.active) {
          ctx.fillStyle = sp.type === 'donut' ? '#FF69B4' : '#00FF00';
          ctx.beginPath();
          ctx.arc(oX + sp.x * cellS, oY + sp.y * cellS, 2, 0, Math.PI * 2);
          ctx.fill();
        }
      });
      ctx.fillStyle = '#FFD700';
      ctx.beginPath();
      ctx.arc(oX + g.px * cellS, oY + g.py * cellS, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#FFD700';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(oX + g.px * cellS, oY + g.py * cellS);
      ctx.lineTo(oX + g.px * cellS + Math.cos(g.pa) * 8, oY + g.py * cellS + Math.sin(g.pa) * 8);
      ctx.stroke();

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [screen]);

  const btnClass = "px-6 py-3 bg-yellow-400 text-gray-900 font-bold rounded-lg hover:bg-pink-400 hover:text-white transition-all transform hover:scale-105 active:scale-95";
  const ctrlBtn = "w-14 h-14 bg-yellow-400 bg-opacity-20 border-2 border-yellow-400 rounded-xl text-white font-bold text-xl flex items-center justify-center active:bg-yellow-400 active:text-gray-900 transition-colors select-none";
  const ctrlBtnPink = "w-14 h-14 bg-pink-400 bg-opacity-20 border-2 border-pink-400 rounded-xl text-white font-bold text-sm flex items-center justify-center active:bg-pink-400 active:text-gray-900 transition-colors select-none";

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 p-4">
      <h1 className="text-4xl font-bold text-yellow-400 mb-1 tracking-wider" style={{ textShadow: '3px 3px 0 #FF69B4, -1px -1px 0 #000' }}>
        🍩 SIMPSONS DOOM 🍩
      </h1>
      <p className="text-pink-300 mb-4 text-sm">Collect donuts • Avoid Flanders • Survive!</p>

      <div className="relative rounded-xl overflow-hidden shadow-2xl" style={{ boxShadow: '0 0 30px rgba(255,105,180,0.3)' }}>
        <canvas ref={canvasRef} width={600} height={380} className="border-4 border-yellow-400" style={{ imageRendering: 'auto' }} />

        {screen === 'menu' && (
          <div className="absolute inset-0 bg-black bg-opacity-85 flex flex-col items-center justify-center">
            <div className="text-7xl mb-4 animate-bounce">🍩</div>
            <h2 className="text-3xl text-yellow-400 mb-2 font-bold">SIMPSONS DOOM</h2>
            <p className="text-pink-300 mb-6">The Ultimate Donut Hunt!</p>
            <button onClick={initGame} className={btnClass}>🎮 START GAME</button>
            <div className="mt-8 text-gray-400 text-sm text-center space-y-1">
              <p><span className="text-yellow-400 font-bold">W/S</span> or <span className="text-yellow-400 font-bold">↑/↓</span> - Move Forward/Back</p>
              <p><span className="text-pink-400 font-bold">A/D</span> - Strafe Left/Right</p>
              <p><span className="text-yellow-400 font-bold">←/→</span> - Turn</p>
            </div>
          </div>
        )}

        {screen === 'victory' && (
          <div className="absolute inset-0 bg-black bg-opacity-90 flex flex-col items-center justify-center">
            <div className="text-7xl mb-4">🎉</div>
            <h2 className="text-3xl text-yellow-400 mb-2 font-bold">WOOHOO!</h2>
            <p className="text-pink-300 text-xl mb-2">All Donuts Collected!</p>
            <p className="text-white mb-6">🍩 {score.donuts} / {score.total}</p>
            <button onClick={initGame} className={btnClass}>🍩 Play Again!</button>
          </div>
        )}

        {screen === 'gameover' && (
          <div className="absolute inset-0 bg-black bg-opacity-90 flex flex-col items-center justify-center">
            <div className="text-7xl mb-4">😫</div>
            <h2 className="text-3xl text-pink-400 mb-2 font-bold">D'OH!</h2>
            <p className="text-gray-300 text-xl mb-2">Flanders Got You!</p>
            <p className="text-white mb-6">🍩 {score.donuts} / {score.total}</p>
            <button onClick={initGame} className={btnClass}>🔄 Try Again!</button>
          </div>
        )}
      </div>

      {screen === 'playing' && (
        <div className="mt-4 flex gap-6 items-center">
          <button
            onMouseDown={() => keysRef.current['arrowleft'] = true}
            onMouseUp={() => keysRef.current['arrowleft'] = false}
            onMouseLeave={() => keysRef.current['arrowleft'] = false}
            onTouchStart={(e) => { e.preventDefault(); keysRef.current['arrowleft'] = true; }}
            onTouchEnd={() => keysRef.current['arrowleft'] = false}
            className={ctrlBtn}
          >◀</button>
          
          <div className="flex flex-col gap-2 items-center">
            <button
              onMouseDown={() => keysRef.current['w'] = true}
              onMouseUp={() => keysRef.current['w'] = false}
              onMouseLeave={() => keysRef.current['w'] = false}
              onTouchStart={(e) => { e.preventDefault(); keysRef.current['w'] = true; }}
              onTouchEnd={() => keysRef.current['w'] = false}
              className={ctrlBtn}
            >▲</button>
            <div className="flex gap-2">
              <button
                onMouseDown={() => keysRef.current['a'] = true}
                onMouseUp={() => keysRef.current['a'] = false}
                onMouseLeave={() => keysRef.current['a'] = false}
                onTouchStart={(e) => { e.preventDefault(); keysRef.current['a'] = true; }}
                onTouchEnd={() => keysRef.current['a'] = false}
                className={ctrlBtnPink}
              >◁</button>
              <button
                onMouseDown={() => keysRef.current['d'] = true}
                onMouseUp={() => keysRef.current['d'] = false}
                onMouseLeave={() => keysRef.current['d'] = false}
                onTouchStart={(e) => { e.preventDefault(); keysRef.current['d'] = true; }}
                onTouchEnd={() => keysRef.current['d'] = false}
                className={ctrlBtnPink}
              >▷</button>
            </div>
            <button
              onMouseDown={() => keysRef.current['s'] = true}
              onMouseUp={() => keysRef.current['s'] = false}
              onMouseLeave={() => keysRef.current['s'] = false}
              onTouchStart={(e) => { e.preventDefault(); keysRef.current['s'] = true; }}
              onTouchEnd={() => keysRef.current['s'] = false}
              className={ctrlBtn}
            >▼</button>
          </div>
          
          <button
            onMouseDown={() => keysRef.current['arrowright'] = true}
            onMouseUp={() => keysRef.current['arrowright'] = false}
            onMouseLeave={() => keysRef.current['arrowright'] = false}
            onTouchStart={(e) => { e.preventDefault(); keysRef.current['arrowright'] = true; }}
            onTouchEnd={() => keysRef.current['arrowright'] = false}
            className={ctrlBtn}
          >▶</button>
        </div>
      )}
      
      <p className="text-gray-500 text-xs mt-4">Use keyboard or touch controls to play</p>
    </div>
  );
}

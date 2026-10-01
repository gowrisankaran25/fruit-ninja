/**
 * FRUIT NINJA - HTML5 Web Application Engine
 * Real-time MediaPipe Hand Tracking with Webcam Mirror Feed & EMA Coordinate Filtering
 */

// Global State
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

let width = window.innerWidth;
let height = window.innerHeight;
canvas.width = width;
canvas.height = height;

window.addEventListener('resize', () => {
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = width;
  canvas.height = height;
});

// Sound Effects (Web Audio API Synthesizer)
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playSound(type) {
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.connect(gain);
  gain.connect(audioCtx.destination);

  const now = audioCtx.currentTime;

  if (type === 'swipe') {
    osc.type = 'sine';
    osc.frequency.setValueAtTime(400, now);
    osc.frequency.exponentialRampToValueAtTime(100, now + 0.15);
    gain.gain.setValueAtTime(0.15, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
    osc.start(now);
    osc.stop(now + 0.15);
  } else if (type === 'slice') {
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(600, now);
    osc.frequency.exponentialRampToValueAtTime(1200, now + 0.1);
    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
    osc.start(now);
    osc.stop(now + 0.1);
  } else if (type === 'bomb') {
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(150, now);
    osc.frequency.exponentialRampToValueAtTime(30, now + 0.4);
    gain.gain.setValueAtTime(0.5, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
    osc.start(now);
    osc.stop(now + 0.4);
  }
}

// Game Configuration & Data
const FRUIT_TYPES = [
  { name: 'apple', color: '#ff3344', juice: '#ff0033', radius: 38, score: 10 },
  { name: 'banana', color: '#ffea00', juice: '#ffd700', radius: 34, score: 15 },
  { name: 'orange', color: '#ff9900', juice: '#ff6600', radius: 36, score: 10 },
  { name: 'watermelon', color: '#22cc55', juice: '#cc0033', radius: 46, score: 20 },
  { name: 'pineapple', color: '#eeaa22', juice: '#ffbb00', radius: 42, score: 25 },
  { name: 'golden', color: '#ffd700', juice: '#ffffff', radius: 30, score: 50, special: true }
];

let gameState = 'MENU'; // MENU, MODE_SELECT, PLAYING, PAUSED, GAMEOVER, ACHIEVEMENTS
let currentMode = 'classic'; // classic, arcade, zen, survival
let score = 0;
let bestScore = parseInt(localStorage.getItem('fn_bestScore') || '0');
let level = 1;
let levelXp = 0;
let lives = 3;
let gameTime = 60;
let lastTime = performance.now();
let comboCount = 0;
let comboTimer = 0;
let maxCombo = 0;
let totalSlices = 0;
let successfulSlices = 0;

// Smooth Tracking (EMA Filter)
let inputMode = 'HAND'; // HAND or MOUSE
let rawTrail = [];
let smoothedTrail = [];
let mousePos = { x: width / 2, y: height / 2 };
let isMouseDown = false;
let filterX = null;
let filterY = null;

// Entities
let fruits = [];
let menuBackgroundFruits = [];
let slicedHalves = [];
let particles = [];
let popups = [];

// Initialize Menu Background Floating Fruits
for (let i = 0; i < 8; i++) {
  menuBackgroundFruits.push({
    x: Math.random() * width,
    y: Math.random() * height,
    radius: 35 + Math.random() * 25,
    color: FRUIT_TYPES[Math.floor(Math.random() * FRUIT_TYPES.length)].color,
    vx: (Math.random() - 0.5) * 60,
    vy: (Math.random() - 0.5) * 60,
    rot: Math.random() * Math.PI * 2,
    vRot: (Math.random() - 0.5) * 2
  });
}

// DOM Elements
const menuScreen = document.getElementById('menu-screen');
const modeScreen = document.getElementById('mode-screen');
const achievementsScreen = document.getElementById('achievements-screen');
const gameoverScreen = document.getElementById('gameover-screen');
const pauseScreen = document.getElementById('pause-screen');
const hudOverlay = document.getElementById('hud-overlay');

const hudScore = document.getElementById('hud-score');
const hudBestScore = document.getElementById('hud-best-score');
const hudModeTag = document.getElementById('hud-mode-tag');
const hudLevelText = document.getElementById('hud-level-text');
const hudXpFill = document.getElementById('hud-xp-fill');
const hudLivesContainer = document.getElementById('hud-lives-container');
const hudTimerCard = document.getElementById('hud-timer-card');
const hudTimerValue = document.getElementById('hud-timer-value');
const hudComboBanner = document.getElementById('hud-combo-banner');
const hudComboText = document.getElementById('hud-combo-text');

const statusInput = document.getElementById('status-input');
const hudStatusInput = document.getElementById('hud-status-input');
const statusCamera = document.getElementById('status-camera');
const hudStatusCamera = document.getElementById('hud-status-camera');

hudBestScore.innerText = bestScore;

// Achievements
const achievements = [
  { id: 'first_slice', title: 'First Blood', desc: 'Slice your very first fruit', unlocked: false, icon: '🗡️' },
  { id: 'combo_3', title: 'Combo Master', desc: 'Perform a 3x or higher combo', unlocked: false, icon: '🔥' },
  { id: 'score_100', title: 'Century Slicer', desc: 'Reach a score of 100 points', unlocked: false, icon: '💯' },
  { id: 'golden_fruit', title: 'Touch of Midas', desc: 'Slice a rare Golden Fruit', unlocked: false, icon: '✨' },
  { id: 'zen_master', title: 'Zen Master', desc: 'Complete a Zen Mode session', unlocked: false, icon: '🧘' }
];

const savedAch = JSON.parse(localStorage.getItem('fn_achievements') || '[]');
achievements.forEach(a => {
  if (savedAch.includes(a.id)) a.unlocked = true;
});

function unlockAchievement(id) {
  const ach = achievements.find(a => a.id === id);
  if (ach && !ach.unlocked) {
    ach.unlocked = true;
    const saved = achievements.filter(a => a.unlocked).map(a => a.id);
    localStorage.setItem('fn_achievements', JSON.stringify(saved));
    showPopup(`🏆 Unlocked: ${ach.title}`, width / 2, height / 3, '#ffd700');
  }
}

// Chaikin Curve Subdivision
function chaikinSmoothing(points, iterations = 2) {
  if (points.length < 3) return points;
  let current = points;
  for (let it = 0; it < iterations; it++) {
    const next = [current[0]];
    for (let i = 0; i < current.length - 1; i++) {
      const p0 = current[i];
      const p1 = current[i + 1];
      const q = { x: 0.75 * p0.x + 0.25 * p1.x, y: 0.75 * p0.y + 0.25 * p1.y };
      const r = { x: 0.25 * p0.x + 0.75 * p1.x, y: 0.25 * p0.y + 0.75 * p1.y };
      next.push(q, r);
    }
    next.push(current[current.length - 1]);
    current = next;
  }
  return current;
}

// Line Segment vs Circle Collision
function segmentHitsCircle(p1, p2, circle) {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const lenSq = dx * dx + dy * dy;

  if (lenSq === 0) {
    const distSq = (p1.x - circle.x) ** 2 + (p1.y - circle.y) ** 2;
    return distSq <= circle.radius ** 2;
  }

  let t = ((circle.x - p1.x) * dx + (circle.y - p1.y) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));

  const closestX = p1.x + t * dx;
  const closestY = p1.y + t * dy;

  const distSq = (closestX - circle.x) ** 2 + (closestY - circle.y) ** 2;
  return distSq <= circle.radius ** 2;
}

// MediaPipe Camera & Hand Landmark Initialization
const videoElement = document.getElementById('webcam');

if (typeof Hands !== 'undefined') {
  const hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
  });

  hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.75,
    minTrackingConfidence: 0.75
  });

  hands.onResults(onHandResults);

  const camera = new Camera(videoElement, {
    onFrame: async () => {
      await hands.send({ image: videoElement });
    },
    width: 640,
    height: 480
  });

  camera.start().then(() => {
    if (statusCamera) statusCamera.innerText = 'CAMERA: READY';
    if (hudStatusCamera) hudStatusCamera.innerText = 'CAMERA: READY';
  }).catch(err => {
    console.warn("Webcam permission denied or camera missing. Defaulting to Mouse mode.", err);
    if (statusCamera) statusCamera.innerText = 'CAMERA: MOUSE MODE';
    if (hudStatusCamera) hudStatusCamera.innerText = 'CAMERA: MOUSE MODE';
    inputMode = 'MOUSE';
    updateInputBadge();
  });
} else {
  inputMode = 'MOUSE';
  updateInputBadge();
}

function onHandResults(results) {
  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    inputMode = 'HAND';
    updateInputBadge();
    const landmarks = results.multiHandLandmarks[0];

    const rawX = (1 - landmarks[8].x) * width; // Mirror X
    const rawY = landmarks[8].y * height;

    // Apply Exponential Moving Average (EMA) smoothing for perfect stability (alpha = 0.3)
    if (filterX === null) {
      filterX = rawX;
      filterY = rawY;
    } else {
      const alpha = 0.3;
      filterX += alpha * (rawX - filterX);
      filterY += alpha * (rawY - filterY);
    }

    addTrailPoint(filterX, filterY);

    const indexTip = landmarks[8];
    const pinkyTip = landmarks[20];
    const handSpan = Math.hypot(pinkyTip.x - indexTip.x, pinkyTip.y - indexTip.y);

    if (handSpan > 0.4 && gameState === 'PLAYING') {
      pauseGame();
    }
  }
}

// Mouse Controls
window.addEventListener('mousemove', (e) => {
  mousePos.x = e.clientX;
  mousePos.y = e.clientY;
  if (inputMode === 'MOUSE' && isMouseDown) {
    addTrailPoint(e.clientX, e.clientY);
  }
});

window.addEventListener('mousedown', (e) => {
  isMouseDown = true;
  if (inputMode === 'MOUSE') {
    playSound('swipe');
    addTrailPoint(e.clientX, e.clientY);
  }
});

window.addEventListener('mouseup', () => {
  isMouseDown = false;
});

window.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    e.preventDefault();
    inputMode = inputMode === 'HAND' ? 'MOUSE' : 'HAND';
    updateInputBadge();
  } else if (e.key === 'Escape' || e.key === ' ') {
    if (gameState === 'PLAYING') pauseGame();
    else if (gameState === 'PAUSED') resumeGame();
  } else if (e.key === 'r' || e.key === 'R') {
    if (gameState === 'GAMEOVER') startGame(currentMode);
  } else if (e.key === 'm' || e.key === 'M') {
    if (gameState === 'GAMEOVER' || gameState === 'PAUSED') showMenu();
  }
});

function updateInputBadge() {
  const text = inputMode === 'HAND' ? 'HAND TRACKING' : 'MOUSE MODE';
  if (statusInput) statusInput.innerText = text;
  if (hudStatusInput) hudStatusInput.innerText = text;
}

function addTrailPoint(x, y) {
  rawTrail.push({ x, y, time: performance.now() });
  if (rawTrail.length > 15) rawTrail.shift();
}

// Fruit Entity Class
class Fruit {
  constructor(typeObj) {
    this.type = typeObj.name;
    this.color = typeObj.color;
    this.juice = typeObj.juice;
    this.radius = typeObj.radius;
    this.score = typeObj.score;
    this.isBomb = typeObj.isBomb || false;
    this.isPowerup = typeObj.isPowerup || false;
    this.special = typeObj.special || false;

    this.x = width * (0.15 + Math.random() * 0.7);
    this.y = height + this.radius + 10;
    
    const targetX = width * (0.3 + Math.random() * 0.4);
    const vx = (targetX - this.x) / 1.5;
    const vy = -(height * 0.75 + Math.random() * (height * 0.15));

    this.vx = vx * 0.95;
    this.vy = vy;
    this.gravity = 650;
    this.rotation = Math.random() * Math.PI * 2;
    this.vRot = (Math.random() - 0.5) * 4;
    this.active = true;
  }

  update(dt) {
    this.x += this.vx * dt;
    this.y += this.vy * dt;
    this.vy += this.gravity * dt;
    this.rotation += this.vRot * dt;

    if (this.y > height + this.radius + 50 && this.vy > 0) {
      this.active = false;
      if (!this.isBomb && !this.isPowerup && gameState === 'PLAYING') {
        if (currentMode === 'classic' || currentMode === 'survival') {
          lives--;
          updateLivesDisplay();
          if (lives <= 0) gameOver();
        }
      }
    }
  }

  draw(ctx) {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.rotation);

    if (this.isBomb) {
      ctx.beginPath();
      ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = '#111122';
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#ff3366';
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(0, -this.radius);
      ctx.quadraticCurveTo(10, -this.radius - 10, 15, -this.radius - 18);
      ctx.strokeStyle = '#eeaa33';
      ctx.lineWidth = 3;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(15, -this.radius - 18, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffff00';
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(-this.radius * 0.3, -this.radius * 0.3, this.radius * 0.35, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.fill();

      if (this.special) {
        ctx.shadowColor = '#ffd700';
        ctx.shadowBlur = 20;
      }
    }

    ctx.restore();
  }
}

// Sliced Half Fruit Entity
class SlicedHalf {
  constructor(x, y, radius, color, juice, angle, side) {
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.color = color;
    this.juice = juice;
    this.rotation = angle;
    this.side = side;

    this.vx = side * (100 + Math.random() * 150);
    this.vy = -(150 + Math.random() * 100);
    this.gravity = 750;
    this.vRot = side * (3 + Math.random() * 5);
    this.alpha = 1.0;
    this.active = true;
  }

  update(dt) {
    this.x += this.vx * dt;
    this.y += this.vy * dt;
    this.vy += this.gravity * dt;
    this.rotation += this.vRot * dt;
    this.alpha -= dt * 0.8;
    if (this.alpha <= 0 || this.y > height + 100) {
      this.active = false;
    }
  }

  draw(ctx) {
    ctx.save();
    ctx.globalAlpha = Math.max(0, this.alpha);
    ctx.translate(this.x, this.y);
    ctx.rotate(this.rotation);

    ctx.beginPath();
    if (this.side < 0) {
      ctx.arc(0, 0, this.radius, Math.PI * 0.5, Math.PI * 1.5);
    } else {
      ctx.arc(0, 0, this.radius, Math.PI * 1.5, Math.PI * 0.5);
    }
    ctx.closePath();
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.stroke();

    ctx.restore();
  }
}

// Particle Splash
class Particle {
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.color = color;
    this.radius = 3 + Math.random() * 5;
    const angle = Math.random() * Math.PI * 2;
    const speed = 100 + Math.random() * 300;
    this.vx = Math.cos(angle) * speed;
    this.vy = Math.sin(angle) * speed;
    this.gravity = 400;
    this.alpha = 1.0;
    this.active = true;
  }

  update(dt) {
    this.x += this.vx * dt;
    this.y += this.vy * dt;
    this.vy += this.gravity * dt;
    this.alpha -= dt * 1.5;
    if (this.alpha <= 0) this.active = false;
  }

  draw(ctx) {
    ctx.save();
    ctx.globalAlpha = Math.max(0, this.alpha);
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.restore();
  }
}

function showPopup(text, x, y, color = '#ffffff') {
  popups.push({ text, x, y, color, alpha: 1.0, vy: -60 });
}

let spawnTimer = 0;

function updateSpawner(dt) {
  spawnTimer += dt;
  const interval = Math.max(0.8, 2.2 - level * 0.15);

  if (spawnTimer >= interval) {
    spawnTimer = 0;
    const count = 1 + Math.floor(Math.random() * (level > 3 ? 3 : 2));
    for (let i = 0; i < count; i++) {
      if (currentMode === 'classic' && Math.random() < 0.25) {
        fruits.push(new Fruit({ name: 'bomb', color: '#111', juice: '#f00', radius: 32, score: 0, isBomb: true }));
      } else {
        const randType = FRUIT_TYPES[Math.floor(Math.random() * FRUIT_TYPES.length)];
        fruits.push(new Fruit(randType));
      }
    }
  }
}

// Main Game Engine Loop
function gameLoop(time) {
  const dt = Math.min((time - lastTime) / 1000, 0.1);
  lastTime = time;

  ctx.clearRect(0, 0, width, height);

  // Render Real-Time Translucent Webcam Video Feed on Canvas (Matches Pygame OpenCV overlay!)
  if (videoElement && videoElement.readyState === 4) {
    ctx.save();
    ctx.globalAlpha = 0.35; // Translucent video feed overlay
    ctx.translate(width, 0);
    ctx.scale(-1, 1); // Mirror video feed horizontally
    ctx.drawImage(videoElement, 0, 0, width, height);
    ctx.restore();
  }

  const now = performance.now();
  rawTrail = rawTrail.filter(p => now - p.time < 200);
  smoothedTrail = chaikinSmoothing(rawTrail, 2);

  // Render Background Floating Fruits on Menu Screen
  if (gameState === 'MENU' || gameState === 'MODE_SELECT' || gameState === 'ACHIEVEMENTS') {
    menuBackgroundFruits.forEach(bf => {
      bf.x += bf.vx * dt;
      bf.y += bf.vy * dt;
      bf.rot += bf.vRot * dt;

      if (bf.x < 0 || bf.x > width) bf.vx *= -1;
      if (bf.y < 0 || bf.y > height) bf.vy *= -1;

      ctx.save();
      ctx.translate(bf.x, bf.y);
      ctx.rotate(bf.rot);
      ctx.beginPath();
      ctx.arc(0, 0, bf.radius, 0, Math.PI * 2);
      ctx.fillStyle = bf.color;
      ctx.globalAlpha = 0.55;
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(-bf.radius * 0.3, -bf.radius * 0.3, bf.radius * 0.3, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';
      ctx.fill();
      ctx.restore();
    });
  }

  if (gameState === 'PLAYING') {
    if (currentMode === 'arcade' || currentMode === 'zen') {
      gameTime -= dt;
      hudTimerValue.innerText = Math.max(0, Math.ceil(gameTime));
      if (gameTime <= 0) {
        if (currentMode === 'zen') unlockAchievement('zen_master');
        gameOver();
      }
    }

    updateSpawner(dt);

    const segmentsToCheck = [];
    if (smoothedTrail.length >= 2) {
      for (let i = 0; i < smoothedTrail.length - 1; i++) {
        segmentsToCheck.push({ p1: smoothedTrail[i], p2: smoothedTrail[i + 1] });
      }
    } else if (smoothedTrail.length === 1 && (isMouseDown || inputMode === 'HAND')) {
      segmentsToCheck.push({ p1: smoothedTrail[0], p2: smoothedTrail[0] });
    }

    if (segmentsToCheck.length > 0) {
      let slicedThisFrame = 0;
      for (const seg of segmentsToCheck) {
        const p1 = seg.p1;
        const p2 = seg.p2;

        fruits.forEach(fruit => {
          if (fruit.active && segmentHitsCircle(p1, p2, fruit)) {
            fruit.active = false;
            totalSlices++;

            if (fruit.isBomb) {
              playSound('bomb');
              particles.push(new Particle(fruit.x, fruit.y, '#ff3300'));
              if (currentMode === 'arcade') {
                score = Math.max(0, score - 10);
                hudScore.innerText = score;
                showPopup('-10 BOMB!', fruit.x, fruit.y, '#ff3366');
              } else {
                gameOver();
              }
            } else {
              playSound('slice');
              successfulSlices++;
              slicedThisFrame++;

              if (fruit.special) unlockAchievement('golden_fruit');
              unlockAchievement('first_slice');

              comboCount++;
              comboTimer = 0.4;
              maxCombo = Math.max(maxCombo, comboCount);

              const gainedScore = fruit.score * (comboCount > 1 ? comboCount : 1);
              score += gainedScore;
              levelXp += gainedScore;

              if (score > bestScore) {
                bestScore = score;
                localStorage.setItem('fn_bestScore', bestScore.toString());
                hudBestScore.innerText = bestScore;
              }

              if (score >= 100) unlockAchievement('score_100');
              if (comboCount >= 3) unlockAchievement('combo_3');

              hudScore.innerText = score;
              showPopup(`+${gainedScore}`, fruit.x, fruit.y, fruit.color);

              slicedHalves.push(new SlicedHalf(fruit.x, fruit.y, fruit.radius, fruit.color, fruit.juice, fruit.rotation, -1));
              slicedHalves.push(new SlicedHalf(fruit.x, fruit.y, fruit.radius, fruit.color, fruit.juice, fruit.rotation, 1));

              for (let k = 0; k < 12; k++) {
                particles.push(new Particle(fruit.x, fruit.y, fruit.juice));
              }

              if (levelXp >= level * 100) {
                levelXp = 0;
                level++;
                hudLevelText.innerText = `LVL ${level}`;
              }
              hudXpFill.style.width = `${Math.min(100, (levelXp / (level * 100)) * 100)}%`;
            }
          }
        });
      }

      if (comboTimer > 0) {
        comboTimer -= dt;
        if (comboTimer <= 0) {
          if (comboCount >= 3) {
            hudComboText.innerText = `${comboCount}x COMBO!`;
            hudComboBanner.classList.remove('hidden');
            setTimeout(() => hudComboBanner.classList.add('hidden'), 1200);
          }
          comboCount = 0;
        }
      }
    }
  }

  // Draw Entities
  fruits.forEach(f => { f.update(dt); f.draw(ctx); });
  fruits = fruits.filter(f => f.active);

  slicedHalves.forEach(h => { h.update(dt); h.draw(ctx); });
  slicedHalves = slicedHalves.filter(h => h.active);

  particles.forEach(p => { p.update(dt); p.draw(ctx); });
  particles = particles.filter(p => p.active);

  popups.forEach((pop) => {
    pop.y += pop.vy * dt;
    pop.alpha -= dt * 1.2;
    ctx.save();
    ctx.globalAlpha = Math.max(0, pop.alpha);
    ctx.font = '900 24px Outfit, sans-serif';
    ctx.fillStyle = pop.color;
    ctx.fillText(pop.text, pop.x, pop.y);
    ctx.restore();
  });
  popups = popups.filter(p => p.alpha > 0);

  // Render Glowing Blade Trail
  if (smoothedTrail.length >= 2) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(smoothedTrail[0].x, smoothedTrail[0].y);
    for (let i = 1; i < smoothedTrail.length; i++) {
      ctx.lineTo(smoothedTrail[i].x, smoothedTrail[i].y);
    }
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = 8;
    ctx.strokeStyle = '#00f0ff';
    ctx.shadowColor = '#00f0ff';
    ctx.shadowBlur = 15;
    ctx.stroke();

    ctx.lineWidth = 3;
    ctx.strokeStyle = '#ffffff';
    ctx.shadowBlur = 0;
    ctx.stroke();
    ctx.restore();

    const tip = smoothedTrail[smoothedTrail.length - 1];
    ctx.save();
    ctx.beginPath();
    ctx.arc(tip.x, tip.y, 6, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = '#00f0ff';
    ctx.shadowBlur = 20;
    ctx.fill();
    ctx.restore();
  }

  requestAnimationFrame(gameLoop);
}

// Navigation & Screen Handlers
function hideAllScreens() {
  menuScreen.classList.add('hidden');
  modeScreen.classList.add('hidden');
  achievementsScreen.classList.add('hidden');
  gameoverScreen.classList.add('hidden');
  pauseScreen.classList.add('hidden');
  hudOverlay.classList.add('hidden');
}

function showMenu() {
  gameState = 'MENU';
  hideAllScreens();
  menuScreen.classList.remove('hidden');
}

function showModeSelect() {
  gameState = 'MODE_SELECT';
  hideAllScreens();
  modeScreen.classList.remove('hidden');
}

function showAchievements() {
  gameState = 'ACHIEVEMENTS';
  hideAllScreens();
  achievementsScreen.classList.remove('hidden');

  const list = document.getElementById('achievements-list');
  list.innerHTML = achievements.map(a => `
    <div class="achievement-item ${a.unlocked ? 'unlocked' : ''}">
      <div class="achievement-icon">${a.icon}</div>
      <div class="achievement-info">
        <h4>${a.title}</h4>
        <p>${a.desc}</p>
      </div>
    </div>
  `).join('');
}

function startGame(mode = 'classic') {
  currentMode = mode;
  score = 0;
  level = 1;
  levelXp = 0;
  lives = mode === 'survival' ? 1 : 3;
  gameTime = mode === 'arcade' ? 60 : (mode === 'zen' ? 90 : 0);
  comboCount = 0;
  maxCombo = 0;
  totalSlices = 0;
  successfulSlices = 0;
  fruits = [];
  slicedHalves = [];
  particles = [];

  hudScore.innerText = '0';
  hudLevelText.innerText = 'LVL 1';
  hudXpFill.style.width = '0%';
  hudModeTag.innerText = `${mode.toUpperCase()} MODE`;

  if (mode === 'arcade' || mode === 'zen') {
    hudTimerCard.classList.remove('hidden');
    hudTimerValue.innerText = gameTime;
  } else {
    hudTimerCard.classList.add('hidden');
  }

  updateLivesDisplay();
  hideAllScreens();
  hudOverlay.classList.remove('hidden');
  gameState = 'PLAYING';
}

function updateLivesDisplay() {
  if (currentMode === 'arcade' || currentMode === 'zen') {
    hudLivesContainer.innerHTML = '';
    return;
  }
  let heartsHtml = '';
  for (let i = 0; i < lives; i++) {
    heartsHtml += '❤️ ';
  }
  hudLivesContainer.innerHTML = heartsHtml;
}

function pauseGame() {
  if (gameState === 'PLAYING') {
    gameState = 'PAUSED';
    pauseScreen.classList.remove('hidden');
  }
}

function resumeGame() {
  if (gameState === 'PAUSED') {
    pauseScreen.classList.add('hidden');
    gameState = 'PLAYING';
  }
}

function gameOver() {
  gameState = 'GAMEOVER';
  hideAllScreens();
  gameoverScreen.classList.remove('hidden');

  document.getElementById('gameover-score').innerText = score;
  const acc = totalSlices > 0 ? Math.round((successfulSlices / totalSlices) * 100) : 100;
  document.getElementById('gameover-accuracy').innerText = `${acc}%`;
  document.getElementById('gameover-combo').innerText = `${maxCombo}x`;

  let rank = 'C-RANK';
  if (score >= 200 && acc >= 80) rank = 'S-RANK';
  else if (score >= 120) rank = 'A-RANK';
  else if (score >= 60) rank = 'B-RANK';

  document.getElementById('gameover-rank').innerText = rank;
}

// Event Listeners for UI Buttons
document.getElementById('btn-start').addEventListener('click', () => startGame(currentMode));
document.getElementById('btn-mode-select').addEventListener('click', showModeSelect);
document.getElementById('btn-achievements').addEventListener('click', showAchievements);
const exitBtn = document.getElementById('btn-exit');
if (exitBtn) {
  exitBtn.addEventListener('click', () => showMenu());
}

document.getElementById('btn-mode-back').addEventListener('click', showMenu);
document.getElementById('btn-achievements-back').addEventListener('click', showMenu);

document.querySelectorAll('.mode-card').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.mode-card').forEach(c => c.classList.remove('active'));
    card.classList.add('active');
    currentMode = card.getAttribute('data-mode');
    startGame(currentMode);
  });
});

document.getElementById('btn-restart').addEventListener('click', () => startGame(currentMode));
document.getElementById('btn-main-menu').addEventListener('click', showMenu);
document.getElementById('btn-resume').addEventListener('click', resumeGame);
document.getElementById('btn-pause-menu').addEventListener('click', showMenu);

// Start Animation Loop
requestAnimationFrame(gameLoop);

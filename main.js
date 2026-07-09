import * as THREE from "https://esm.sh/three@0.164.1";
import { OrbitControls } from "https://esm.sh/three@0.164.1/examples/jsm/controls/OrbitControls.js";
import { RoundedBoxGeometry } from "https://esm.sh/three@0.164.1/examples/jsm/geometries/RoundedBoxGeometry.js";

const sceneRoot = document.getElementById("scene-root");
const statusBox = document.getElementById("status-box");
const moveButtons = document.getElementById("move-buttons");
const shuffleBtn = document.getElementById("shuffle-btn");

const scene = new THREE.Scene();
scene.background = new THREE.Color("#202327");

const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(6.4, 5.5, 6.8);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
sceneRoot.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 0, 0);
controls.minDistance = 5;
controls.maxDistance = 14;
controls.update();

const ambient = new THREE.AmbientLight(0xffffff, 0.35);
scene.add(ambient);

const key = new THREE.DirectionalLight(0xffffff, 0.85);
key.position.set(6, 9, 5);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.left = -12;
key.shadow.camera.right = 12;
key.shadow.camera.top = 12;
key.shadow.camera.bottom = -12;
scene.add(key);

const rim = new THREE.DirectionalLight(0xa8c8ff, 0.3);
rim.position.set(-7, 4, -6);
scene.add(rim);

const floorGeo = new THREE.PlaneGeometry(30, 30);
const floorMat = new THREE.MeshStandardMaterial({
  color: "#16181d",
  roughness: 0.98,
  metalness: 0.02
});
const floor = new THREE.Mesh(floorGeo, floorMat);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -2.55;
floor.receiveShadow = true;
scene.add(floor);

const cubeGroup = new THREE.Group();
scene.add(cubeGroup);

const cubies = [];
const spacing = 1.04;
const black = new THREE.Color("#0b0c0d");
const colorMap = {
  px: new THREE.Color("#f57c1f"), // Right orange
  nx: new THREE.Color("#db1d26"), // Left red
  py: new THREE.Color("#ffffff"), // Top white
  ny: new THREE.Color("#ffd22f"), // Bottom yellow
  pz: new THREE.Color("#2f7bff"), // Front blue
  nz: new THREE.Color("#3db959")  // Back green
};

const roundedGeo = new RoundedBoxGeometry(0.94, 0.94, 0.94, 4, 0.08);
const stickerGeo = new THREE.PlaneGeometry(0.68, 0.68);
const cubieBodyMaterial = new THREE.MeshStandardMaterial({
  color: black,
  roughness: 0.94,
  metalness: 0.04
});

function createSticker(color, position, rotation) {
  const sticker = new THREE.Mesh(
    stickerGeo,
    new THREE.MeshStandardMaterial({
      color,
      roughness: 0.86,
      metalness: 0.05,
      emissive: 0x000000,
      emissiveIntensity: 0
    })
  );
  sticker.position.copy(position);
  sticker.rotation.set(rotation.x, rotation.y, rotation.z);
  return sticker;
}

function createCubie(x, y, z) {
  const cubie = new THREE.Mesh(roundedGeo, cubieBodyMaterial.clone());
  cubie.castShadow = true;
  cubie.receiveShadow = true;

  const stickerOffset = 0.476;
  if (x === 1) {
    cubie.add(createSticker(colorMap.px, new THREE.Vector3(stickerOffset, 0, 0), new THREE.Vector3(0, Math.PI / 2, 0)));
  }
  if (x === -1) {
    cubie.add(createSticker(colorMap.nx, new THREE.Vector3(-stickerOffset, 0, 0), new THREE.Vector3(0, -Math.PI / 2, 0)));
  }
  if (y === 1) {
    cubie.add(createSticker(colorMap.py, new THREE.Vector3(0, stickerOffset, 0), new THREE.Vector3(-Math.PI / 2, 0, 0)));
  }
  if (y === -1) {
    cubie.add(createSticker(colorMap.ny, new THREE.Vector3(0, -stickerOffset, 0), new THREE.Vector3(Math.PI / 2, 0, 0)));
  }
  if (z === 1) {
    cubie.add(createSticker(colorMap.pz, new THREE.Vector3(0, 0, stickerOffset), new THREE.Vector3(0, 0, 0)));
  }
  if (z === -1) {
    cubie.add(createSticker(colorMap.nz, new THREE.Vector3(0, 0, -stickerOffset), new THREE.Vector3(0, Math.PI, 0)));
  }

  return cubie;
}

for (let x = -1; x <= 1; x += 1) {
  for (let y = -1; y <= 1; y += 1) {
    for (let z = -1; z <= 1; z += 1) {
      const cubie = createCubie(x, y, z);
      cubie.position.set(x * spacing, y * spacing, z * spacing);
      cubeGroup.add(cubie);
      cubies.push(cubie);
    }
  }
}

let activeMove = null;
const moveQueue = [];

const moveDefs = {
  U: { axis: "y", selector: (p) => p.y > spacing * 0.5, dir: -1 },
  "U'": { axis: "y", selector: (p) => p.y > spacing * 0.5, dir: 1 },
  D: { axis: "y", selector: (p) => p.y < -spacing * 0.5, dir: 1 },
  "D'": { axis: "y", selector: (p) => p.y < -spacing * 0.5, dir: -1 },
  R: { axis: "x", selector: (p) => p.x > spacing * 0.5, dir: -1 },
  "R'": { axis: "x", selector: (p) => p.x > spacing * 0.5, dir: 1 },
  L: { axis: "x", selector: (p) => p.x < -spacing * 0.5, dir: 1 },
  "L'": { axis: "x", selector: (p) => p.x < -spacing * 0.5, dir: -1 },
  F: { axis: "z", selector: (p) => p.z > spacing * 0.5, dir: -1 },
  "F'": { axis: "z", selector: (p) => p.z > spacing * 0.5, dir: 1 },
  B: { axis: "z", selector: (p) => p.z < -spacing * 0.5, dir: 1 },
  "B'": { axis: "z", selector: (p) => p.z < -spacing * 0.5, dir: -1 }
};

function queueMove(move) {
  if (!moveDefs[move]) return;
  moveQueue.push(move);
}

function enqueueSequence(sequence) {
  sequence.forEach((m) => moveQueue.push(m));
}

function startMove(moveName, duration = 320) {
  const def = moveDefs[moveName];
  if (!def) return;

  const pivot = new THREE.Group();
  cubeGroup.add(pivot);

  const moving = cubies.filter((c) => {
    const p = c.position.clone();
    return def.selector(p);
  });

  moving.forEach((c) => pivot.attach(c));

  const axisVec = new THREE.Vector3(
    def.axis === "x" ? 1 : 0,
    def.axis === "y" ? 1 : 0,
    def.axis === "z" ? 1 : 0
  );

  activeMove = {
    moveName,
    pivot,
    moving,
    axisVec,
    duration,
    elapsed: 0,
    target: (Math.PI / 2) * def.dir,
    prevAngle: 0
  };

  if (moveName === "U" || moveName === "U'") {
    moving.forEach((m) => {
      m.traverse((node) => {
        if (node.isMesh && node.material && "emissiveIntensity" in node.material) {
          node.material.emissive = new THREE.Color("#1f4a8f");
          node.material.emissiveIntensity = 0.08;
        }
      });
    });
  }
}

function finishMove() {
  const { pivot, moving, axisVec, target } = activeMove;
  const correction = target - activeMove.prevAngle;
  pivot.rotateOnAxis(axisVec, correction);

  const snapAngle = (a) => Math.round(a / (Math.PI / 2)) * (Math.PI / 2);

  moving.forEach((c) => {
    cubeGroup.attach(c);
    c.position.set(
      Math.round(c.position.x / spacing) * spacing,
      Math.round(c.position.y / spacing) * spacing,
      Math.round(c.position.z / spacing) * spacing
    );

    c.rotation.set(snapAngle(c.rotation.x), snapAngle(c.rotation.y), snapAngle(c.rotation.z));

    c.traverse((node) => {
      if (node.isMesh && node.material && "emissiveIntensity" in node.material) {
        node.material.emissiveIntensity = 0;
      }
    });
  });

  cubeGroup.remove(pivot);
  activeMove = null;
}

function updateMove(dt) {
  if (!activeMove) return;
  activeMove.elapsed += dt;
  const t = Math.min(activeMove.elapsed / activeMove.duration, 1);
  const ease = 1 - Math.pow(1 - t, 3);
  const currentAngle = activeMove.target * ease;
  const delta = currentAngle - activeMove.prevAngle;
  activeMove.prevAngle = currentAngle;
  activeMove.pivot.rotateOnAxis(activeMove.axisVec, delta);

  if (t >= 1) finishMove();
}

function compressTurns(tokens) {
  const out = [];
  tokens.forEach((tok) => {
    if (tok.endsWith("2")) {
      const base = tok.slice(0, -1);
      out.push(base, base);
    } else {
      out.push(tok);
    }
  });
  return out;
}

function generateScramble(length = 18) {
  const faces = ["U", "D", "R", "L", "F", "B"];
  const modifiers = ["", "'"];
  const out = [];
  while (out.length < length) {
    const face = faces[Math.floor(Math.random() * faces.length)];
    const mod = modifiers[Math.floor(Math.random() * modifiers.length)];
    const token = `${face}${mod}`;
    const prevFace = out.length ? out[out.length - 1][0] : "";
    if (face === prevFace) continue;
    out.push(token);
  }
  return out;
}

function setupButtons() {
  const buttonMoves = ["U", "U'", "R", "R'", "F", "F'", "D", "D'", "L", "L'", "B", "B'"];
  buttonMoves.forEach((mv) => {
    const btn = document.createElement("button");
    btn.className = "move-btn";
    btn.textContent = mv;
    btn.addEventListener("click", () => queueMove(mv));
    moveButtons.appendChild(btn);
  });
}

setupButtons();

shuffleBtn.addEventListener("click", () => {
  const scrambleMoves = generateScramble();
  statusBox.textContent = `Scrambled Sequence: Generated`;
  enqueueSequence(scrambleMoves);
});

// Remove initialState scramble so you start with a clean cube to paint
statusBox.textContent = "Cube ready to paint or solve!";


// ==========================================
// --- NEW: INTERACTIVE PAINTING & SOLVING ---
// ==========================================

let activeColor = new THREE.Color("#ffffff"); 

// 1. Color Palette UI Logic
const swatches = document.querySelectorAll('.color-swatch');
swatches.forEach(swatch => {
    swatch.addEventListener('click', (e) => {
        // Remove selection border from all
        swatches.forEach(s => s.style.border = "2px solid transparent");
        // Add to active
        e.target.style.border = "2px solid white";
        activeColor = new THREE.Color(e.target.dataset.color);
    });
});

// 2. Raycaster for clicking 3D stickers
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

window.addEventListener('pointerdown', (event) => {
    // Ignore clicks if they happen on the UI panels
    if (event.target.closest('.panel')) return;

    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);

    // Look for intersections with the stickers (children of the cubeGroup)
    const intersects = raycaster.intersectObjects(cubeGroup.children, true);
    for (let i = 0; i < intersects.length; i++) {
        const object = intersects[i].object;
        if (object.geometry === stickerGeo) {
            // Paint the sticker!
            object.material.color.copy(activeColor);
            break;
        }
    }
});


// ==========================================
// --- AUTOMATED CAMERA SCANNING ---
// ==========================================

// Map Python OpenCV string names to your Three.js hex colors
const cvColorMap = {
    "Red": colorMap.nx,
    "Orange": colorMap.px,
    "Yellow": colorMap.ny,
    "Green": colorMap.nz,
    "Blue": colorMap.pz,
    "White": colorMap.py,
    "Unknown": new THREE.Color("#555555")
};

// Setup Camera Snap Buttons
const cameraButtonsContainer = document.getElementById("camera-buttons");
const faceTargets = [
  { id: "Front", pos: new THREE.Vector3(0, 0, 11) },
  { id: "Right", pos: new THREE.Vector3(11, 0, 0) },
  { id: "Back",  pos: new THREE.Vector3(0, 0, -11) },
  { id: "Left",  pos: new THREE.Vector3(-11, 0, 0) },
  { id: "Top",   pos: new THREE.Vector3(0, 11, 0.01) }, 
  { id: "Bot",   pos: new THREE.Vector3(0, -11, 0.01) }
];

let camAnim = null;

faceTargets.forEach(face => {
  const btn = document.createElement("button");
  btn.textContent = face.id;
  btn.style.flex = "1 0 30%";
  btn.style.padding = "5px";
  btn.style.backgroundColor = "#2b5c8f";
  btn.style.color = "white";
  btn.style.border = "none";
  btn.style.cursor = "pointer";
  
  btn.addEventListener("click", () => {
    const startPos = camera.position.clone();
    const duration = 500;
    const startTime = performance.now();

    if (camAnim) cancelAnimationFrame(camAnim);

    function animateCam(time) {
      let t = (time - startTime) / duration;
      if (t >= 1) t = 1;
      const ease = 1 - Math.pow(1 - t, 3);
      camera.position.lerpVectors(startPos, face.pos, ease);
      controls.update();

      if (t < 1) camAnim = requestAnimationFrame(animateCam);
    }
    camAnim = requestAnimationFrame(animateCam);
  });
  
  cameraButtonsContainer.appendChild(btn);
});

// Setup Scan Button Logic (Fetches from Python)
document.getElementById('scan-btn').addEventListener("click", async () => {
    if (activeMove || moveQueue.length > 0) return; 

    statusBox.textContent = "Fetching colors from Python OpenCV...";
    
    try {
        const res = await fetch("http://127.0.0.1:5000/api/cube-colors");
        if (!res.ok) throw new Error("Network response was not ok");
        const data = await res.json();

        if (!Array.isArray(data) || data.length < 9) {
            throw new Error("Invalid data from OpenCV");
        }

        // Find stickers facing the camera
        const cameraPos = new THREE.Vector3();
        camera.getWorldPosition(cameraPos);
        const facingStickers = [];

        const worldQuat = new THREE.Quaternion();
        const worldNormal = new THREE.Vector3();
        const worldPos = new THREE.Vector3();
        const toCamera = new THREE.Vector3();

        cubies.forEach(cubie => {
            cubie.children.forEach(child => {
                if (child.geometry === stickerGeo) {
                    child.getWorldQuaternion(worldQuat);
                    worldNormal.set(0, 0, 1).applyQuaternion(worldQuat);
                    
                    child.getWorldPosition(worldPos);
                    toCamera.subVectors(cameraPos, worldPos).normalize();

                    if (worldNormal.dot(toCamera) > 0.8) {
                        facingStickers.push(child);
                    }
                }
            });
        });

        if (facingStickers.length !== 9) {
            statusBox.textContent = "Please align the camera to look directly at one face!";
            return;
        }

        // Screen-space sorting
        const posA = new THREE.Vector3();
        const posB = new THREE.Vector3();

        facingStickers.sort((a, b) => {
            a.getWorldPosition(posA).project(camera);
            b.getWorldPosition(posB).project(camera);

            if (Math.abs(posA.y - posB.y) > 0.1) {
                return posB.y - posA.y; 
            }
            return posA.x - posB.x;
        });

        // Apply colors
        for (let i = 0; i < 9; i++) {
            const targetColor = cvColorMap[data[i].color] || cvColorMap["Unknown"];
            facingStickers[i].material.color.copy(targetColor);
        }

        statusBox.textContent = "Face updated! Use palette to fix errors.";
        
    } catch (err) {
        console.error(err);
        statusBox.textContent = "Error fetching colors. Is Python app.py running?";
    }
});


// 3. Helper function: Find the exact center color of a given face
function getCenterColorHex(normalAxis, normalDir) {
    let hex = "";
    cubies.forEach(cubie => {
        // Find the center piece coordinate (e.g. x=0, y=1, z=0 for Top/U face)
        if (Math.round(cubie.position[normalAxis] / spacing) === normalDir &&
            Math.round(cubie.position[normalAxis === 'x' ? 'y' : 'x'] / spacing) === 0 &&
            Math.round(cubie.position[normalAxis === 'z' ? 'y' : 'z'] / spacing) === 0) {
            
            cubie.children.forEach(child => {
                if (child.geometry === stickerGeo) {
                    const worldNormal = new THREE.Vector3(0,0,1).applyQuaternion(child.getWorldQuaternion(new THREE.Quaternion()));
                    if (Math.round(worldNormal[normalAxis]) === normalDir) {
                        hex = child.material.color.getHexString();
                    }
                }
            });
        }
    });
    return hex;
}

// 4. Solve Button Logic
document.getElementById('solve-btn').addEventListener('click', async () => {
    if (activeMove || moveQueue.length > 0) return;
    statusBox.textContent = "Extracting cube state...";

    // Map whatever colors the user painted on the centers to the official URFDLB letters
    const colorToFace = {};
    colorToFace[getCenterColorHex('y', 1)] = 'U';
    colorToFace[getCenterColorHex('x', 1)] = 'R';
    colorToFace[getCenterColorHex('z', 1)] = 'F';
    colorToFace[getCenterColorHex('y', -1)] = 'D';
    colorToFace[getCenterColorHex('x', -1)] = 'L';
    colorToFace[getCenterColorHex('z', -1)] = 'B';

    // Math for sorting the 3D spatial coordinates exactly how Kociemba reads a cube
    const facesToExtract = [
        // Top-to-bottom, Left-to-right math for every face
        { name: 'U', norm: new THREE.Vector3(0, 1, 0), sort: (a,b) => Math.round(a.p.z*10 - b.p.z*10) || Math.round(a.p.x*10 - b.p.x*10) },
        { name: 'R', norm: new THREE.Vector3(1, 0, 0), sort: (a,b) => Math.round(b.p.y*10 - a.p.y*10) || Math.round(b.p.z*10 - a.p.z*10) },
        { name: 'F', norm: new THREE.Vector3(0, 0, 1), sort: (a,b) => Math.round(b.p.y*10 - a.p.y*10) || Math.round(a.p.x*10 - b.p.x*10) },
        { name: 'D', norm: new THREE.Vector3(0, -1, 0), sort: (a,b) => Math.round(b.p.z*10 - a.p.z*10) || Math.round(a.p.x*10 - b.p.x*10) },
        { name: 'L', norm: new THREE.Vector3(-1, 0, 0), sort: (a,b) => Math.round(b.p.y*10 - a.p.y*10) || Math.round(a.p.z*10 - b.p.z*10) },
        { name: 'B', norm: new THREE.Vector3(0, 0, -1), sort: (a,b) => Math.round(b.p.y*10 - a.p.y*10) || Math.round(b.p.x*10 - a.p.x*10) },
    ];

    let kociembaString = "";

    facesToExtract.forEach(faceDef => {
        let faceStickers = [];
        
        cubies.forEach(cubie => {
            cubie.children.forEach(child => {
                if (child.geometry === stickerGeo) {
                    const worldNormal = new THREE.Vector3(0,0,1).applyQuaternion(child.getWorldQuaternion(new THREE.Quaternion()));
                    if (worldNormal.distanceTo(faceDef.norm) < 0.1) {
                        const worldPos = child.getWorldPosition(new THREE.Vector3());
                        faceStickers.push({ p: worldPos, color: child.material.color.getHexString() });
                    }
                }
            });
        });

        faceStickers.sort(faceDef.sort);

        faceStickers.forEach(sticker => {
            const letter = colorToFace[sticker.color];
            kociembaString += letter ? letter : "?"; 
        });
    });

    if (kociembaString.includes("?")) {
        statusBox.textContent = "Error: Some painted colors do not match the center pieces!";
        return;
    }

    // 5. Send string to your Python API
    statusBox.textContent = "Asking Python to solve...";
    try {
        const response = await fetch('http://127.0.0.1:5000/api/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cube_string: kociembaString })
        });

        const result = await response.json();
        
        if (result.error) {
            statusBox.textContent = "Unsolvable state: " + result.error;
        } else {
            const moves = result.moves;
            statusBox.textContent = `Solving in ${moves.length} moves!`;
            
            // Re-format Python's [R2] into JS's [R, R]
            const formattedSequence = compressTurns(moves);
            
            // Animate it!
            enqueueSequence(formattedSequence);
        }
    } catch (err) {
        statusBox.textContent = "Failed to connect. Is Python running?";
        console.error(err);
    }
});

// ==========================================
// --- RENDER LOOP ---
// ==========================================

const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);

  const dt = clock.getDelta() * 1000;

  if (!activeMove && moveQueue.length) {
    const next = moveQueue.shift();
    startMove(next);
  }

  updateMove(dt);
  controls.update();
  renderer.render(scene, camera);
}

animate();

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
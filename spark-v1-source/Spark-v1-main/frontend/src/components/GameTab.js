import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './GameTab.css';

const API = process.env.REACT_APP_BACKEND_URL + '/api';
const CANVAS_SIZE = 800;
const CELL_SIZE = 32; // Vaste zoom - ingezoomd voor building visibility

function GameTab() {
  const [gameState, setGameState] = useState(null);
  const [factionData, setFactionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [followTarget, setFollowTarget] = useState('spark'); // Camera follow target: 'spark' | 'king_gaia' | etc.
  const [cameraMode, setCameraMode] = useState('follow'); // 'follow' | 'free'
  const [freeCameraPos, setFreeCameraPos] = useState({ x: 100, y: 100 }); // Free camera position
  const [activeFaction, setActiveFaction] = useState('spark'); // Which faction's vision to show (FOG OF WAR)
  const [showLegend, setShowLegend] = useState(false);
  const [legendPos, setLegendPos] = useState(() => {
    const saved = localStorage.getItem('legend_button_position');
    return saved ? JSON.parse(saved) : { x: 20, y: window.innerHeight - 80 };
  });
  const [isDragging, setIsDragging] = useState(false);
  const [layoutEditMode, setLayoutEditMode] = useState(false);
  const [minimapSize, setMinimapSize] = useState(() => {
    const saved = localStorage.getItem('minimap_size');
    return saved ? parseInt(saved) : 120;
  });
  const [minimapPos, setMinimapPos] = useState(() => {
    const saved = localStorage.getItem('minimap_position');
    return saved ? JSON.parse(saved) : null; // null = default position
  });
  
  // Audio button state (versleepbaar zoals legenda-knop)
  const [audioButtonPos, setAudioButtonPos] = useState(() => {
    const saved = localStorage.getItem('audio_button_position');
    return saved ? JSON.parse(saved) : { x: window.innerWidth - 80, y: 20 };
  });
  const [isAudioDragging, setIsAudioDragging] = useState(false);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  
  const canvasRef = useRef(null);
  const ambientAudioRef = useRef(null);
  
  // Legenda placement mode
  const [placementMode, setPlacementMode] = useState(null); // { type: 'tree', icon: '🌳' }
  const [placementPreview, setPlacementPreview] = useState(null); // {x, y} grid coordinates for preview highlight
  
  // Handle canvas click for item placement
  const handleCanvasClick = async (e) => {
    if (!gameState) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    
    const gridSize = gameState.grid_size;
    const minimapSizeVal = minimapSize;
    const minimapX = minimapPos ? minimapPos.x : (CANVAS_SIZE - minimapSizeVal - 10);
    const minimapY = minimapPos ? minimapPos.y : 10;
    
    // Check if click is on minimap
    if (clickX >= minimapX && clickX <= minimapX + minimapSizeVal &&
        clickY >= minimapY && clickY <= minimapY + minimapSizeVal) {
      
      // Convert minimap click to world coordinates
      const pixelPerTile = minimapSizeVal / gridSize;
      const worldX = Math.floor((clickX - minimapX) / pixelPerTile);
      const worldY = Math.floor((clickY - minimapY) / pixelPerTile);
      
      console.log(`[MINIMAP] Click at world (${worldX}, ${worldY})`);
      
      // Jump camera to clicked location (switch to free camera mode)
      setCameraMode('free');
      setFreeCameraPos({ x: worldX, y: worldY });
      console.log(`✅ Camera jumped to (${worldX}, ${worldY})`);
      return;
    }
    
    // If not on minimap and no placement mode, just return
    if (!placementMode) return;
    
    // Convert to grid coordinates (use same logic as drawGame)
    const spark = gameState.spark;
    const viewWidth = CANVAS_SIZE / CELL_SIZE;
    const viewHeight = CANVAS_SIZE / CELL_SIZE;
    
    let cameraX, cameraY;
    
    if (cameraMode === 'free') {
      cameraX = freeCameraPos.x - viewWidth / 2;
      cameraY = freeCameraPos.y - viewHeight / 2;
    } else {
      // Find follow entity
      let followEntity = spark;
      if (followTarget !== 'spark') {
        const kingBot = gameState.worker_bots?.find(bot => bot.blueprint_id === followTarget);
        if (kingBot) {
          followEntity = kingBot;
        }
      }
      
      cameraX = followEntity.x - viewWidth / 2;
      cameraY = followEntity.y - viewHeight / 2;
    }
    
    cameraX = Math.max(0, Math.min(gridSize - viewWidth, cameraX));
    cameraY = Math.max(0, Math.min(gridSize - viewHeight, cameraY));
    
    const gridX = Math.floor(clickX / CELL_SIZE + cameraX);
    const gridY = Math.floor(clickY / CELL_SIZE + cameraY);
    
    console.log(`[PLACEMENT] ${placementMode.name} at (${gridX}, ${gridY})`);
    
    // Call API to place item
    try {
      const response = await axios.post(`${API}/game/admin/place-item`, {
        type: placementMode.type,
        x: gridX,
        y: gridY
      });
      
      if (response.data.success) {
        console.log(`✅ ${placementMode.name} placed!`);
        // Refresh game state
        fetchGameState();
      } else {
        console.error('❌ Placement failed:', response.data.message);
      }
    } catch (err) {
      console.error('❌ Placement error:', err);
    }
    
    // Clear placement mode after placing
    setPlacementMode(null);
    setPlacementPreview(null);
  };
  
  // Handle canvas mouse move for placement preview
  const handleCanvasMouseMove = (e) => {
    if (!placementMode || !gameState) {
      setPlacementPreview(null);
      return;
    }
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Convert to grid coordinates (same logic as handleCanvasClick)
    const spark = gameState.spark;
    const viewWidth = CANVAS_SIZE / CELL_SIZE;
    const viewHeight = CANVAS_SIZE / CELL_SIZE;
    const gridSize = gameState.grid_size;
    
    let cameraX, cameraY;
    
    if (cameraMode === 'free') {
      cameraX = freeCameraPos.x - viewWidth / 2;
      cameraY = freeCameraPos.y - viewHeight / 2;
    } else {
      let followEntity = spark;
      if (followTarget !== 'spark') {
        const kingBot = gameState.worker_bots?.find(bot => bot.blueprint_id === followTarget);
        if (kingBot) {
          followEntity = kingBot;
        }
      }
      cameraX = followEntity.x - viewWidth / 2;
      cameraY = followEntity.y - viewHeight / 2;
    }
    
    cameraX = Math.max(0, Math.min(gridSize - viewWidth, cameraX));
    cameraY = Math.max(0, Math.min(gridSize - viewHeight, cameraY));
    
    // Grid cell under mouse
    const gridX = Math.floor(mouseX / CELL_SIZE + cameraX);
    const gridY = Math.floor(mouseY / CELL_SIZE + cameraY);
    
    setPlacementPreview({ x: gridX, y: gridY });
  };

  const fetchGameState = async () => {
    try {
      const response = await axios.get(`${API}/game/state`);
      if (response.data.success) {
        setGameState(response.data.state);
        setError(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchFactionData = async () => {
    try {
      const response = await axios.get(`${API}/game/buildings-overview`);
      if (response.data.success) {
        setFactionData(response.data);
      }
    } catch (err) {
      console.error('Error fetching faction data:', err);
    }
  };

  useEffect(() => {
    fetchGameState();
    fetchFactionData();
    const interval = setInterval(() => {
      fetchGameState();
      fetchFactionData();
    }, 2000);
    
    // Start ambient audio SIMPLE way (works!)
    const startAmbient = () => {
      try {
        const ambient = new Audio('/sounds/ambient_birds.wav');
        ambient.volume = 0.3;
        ambient.loop = true;
        ambient.play().then(() => {
          console.log('✅ Ambient audio started');
          setIsAudioPlaying(true);
        }).catch(err => {
          console.log('⚠️ Ambient autoplay blocked:', err.message);
          console.log('👉 Klik "🎵" button om audio te starten');
          setIsAudioPlaying(false);
        });
        
        // Store reference for cleanup
        ambientAudioRef.current = ambient;
      } catch (err) {
        console.error('Audio error:', err);
        setIsAudioPlaying(false);
      }
    };
    
    // Start audio after small delay
    setTimeout(startAmbient, 500);
    
    return () => {
      clearInterval(interval);
      // Stop audio on cleanup
      if (ambientAudioRef.current) {
        ambientAudioRef.current.pause();
        ambientAudioRef.current = null;
      }
    };
  }, []);

  // Camera follow logic - follow Spark OR koning bots
  useEffect(() => {
    if (!gameState || cameraMode !== 'follow') return;
    
    let targetEntity = null;
    
    if (followTarget === 'spark') {
      targetEntity = gameState.spark;
    } else if (followTarget && followTarget.startsWith('king_')) {
      // Find koning bot by name/faction
      const entities = gameState.entities || [];
      const factionName = followTarget.split('_')[1]; // e.g. 'gaia' from 'king_gaia'
      targetEntity = entities.find(e => 
        e.type === 'king' && 
        (e.name?.toLowerCase().includes(factionName) || e.faction === factionName)
      );
      
      if (!targetEntity) {
        console.warn(`Koning ${followTarget} not found in entities`);
      }
    }
    
    if (targetEntity) {
      setFreeCameraPos({ x: targetEntity.x, y: targetEntity.y });
    }
  }, [gameState, followTarget, cameraMode]);


  // Keyboard controls for free camera
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!gameState) return;
      
      const moveSpeed = 2; // Tiles per keypress
      const gridSize = gameState.grid_size;
      
      // WASD or Arrow keys for camera movement
      if (e.key === 'w' || e.key === 'W' || e.key === 'ArrowUp') {
        e.preventDefault();
        setCameraMode('free');
        setFreeCameraPos(prev => ({ 
          x: prev.x, 
          y: Math.max(0, prev.y - moveSpeed) 
        }));
      } else if (e.key === 's' || e.key === 'S' || e.key === 'ArrowDown') {
        e.preventDefault();
        setCameraMode('free');
        setFreeCameraPos(prev => ({ 
          x: prev.x, 
          y: Math.min(gridSize - 1, prev.y + moveSpeed) 
        }));
      } else if (e.key === 'a' || e.key === 'A' || e.key === 'ArrowLeft') {
        e.preventDefault();
        setCameraMode('free');
        setFreeCameraPos(prev => ({ 
          x: Math.max(0, prev.x - moveSpeed), 
          y: prev.y 
        }));
      } else if (e.key === 'd' || e.key === 'D' || e.key === 'ArrowRight') {
        e.preventDefault();
        setCameraMode('free');
        setFreeCameraPos(prev => ({ 
          x: Math.min(gridSize - 1, prev.x + moveSpeed), 
          y: prev.y 
        }));
      } else if (e.key === ' ' || e.key === 'Spacebar') {
        // Spacebar: Return to follow Spark
        e.preventDefault();
        setCameraMode('follow');
        setFollowTarget('spark');
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [gameState]);

  useEffect(() => {
    if (gameState && canvasRef.current) {
      drawGame();
    }
  }, [gameState]);

  // Handle legend button dragging
  const handleMouseDown = (e) => {
    setIsDragging(true);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const newX = Math.max(10, Math.min(window.innerWidth - 70, e.clientX - 28));
    const newY = Math.max(10, Math.min(window.innerHeight - 70, e.clientY - 28));
    
    setLegendPos({ x: newX, y: newY });
  };

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false);
      localStorage.setItem('legend_button_position', JSON.stringify(legendPos));
    }
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, legendPos]);

  // Audio button dragging handlers
  const handleAudioMouseDown = (e) => {
    setIsAudioDragging(true);
    e.preventDefault();
  };

  const handleAudioMouseMove = (e) => {
    if (!isAudioDragging) return;
    
    const newX = Math.max(10, Math.min(window.innerWidth - 70, e.clientX - 28));
    const newY = Math.max(10, Math.min(window.innerHeight - 70, e.clientY - 28));
    
    setAudioButtonPos({ x: newX, y: newY });
  };

  const handleAudioMouseUp = () => {
    if (isAudioDragging) {
      setIsAudioDragging(false);
      localStorage.setItem('audio_button_position', JSON.stringify(audioButtonPos));
    }
  };

  useEffect(() => {
    if (isAudioDragging) {
      document.addEventListener('mousemove', handleAudioMouseMove);
      document.addEventListener('mouseup', handleAudioMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleAudioMouseMove);
        document.removeEventListener('mouseup', handleAudioMouseUp);
      };
    }
  }, [isAudioDragging, audioButtonPos]);

  // Audio toggle handler
  const handleAudioToggle = () => {
    // If no audio ref exists, create new audio
    if (!ambientAudioRef.current) {
      const ambient = new Audio('/sounds/ambient_birds.wav');
      ambient.volume = 0.3;
      ambient.loop = true;
      ambient.play();
      ambientAudioRef.current = ambient;
      setIsAudioPlaying(true);
      console.log('🔊 Audio created and playing');
      return;
    }
    
    // If audio exists, toggle play/pause
    if (ambientAudioRef.current.paused) {
      ambientAudioRef.current.play();
      setIsAudioPlaying(true);
      console.log('🔊 Audio resumed');
    } else {
      ambientAudioRef.current.pause();
      setIsAudioPlaying(false);
      console.log('🔇 Audio paused');
    }
  };

  const drawGame = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const gridSize = gameState.grid_size;
    const spark = gameState.spark;

    // CAMERA SYSTEM: Follow mode of Free camera mode
    const viewWidth = CANVAS_SIZE / CELL_SIZE;
    const viewHeight = CANVAS_SIZE / CELL_SIZE;
    
    let cameraX, cameraY;
    
    if (cameraMode === 'free') {
      // FREE CAMERA: User controlled position
      cameraX = freeCameraPos.x - viewWidth / 2;
      cameraY = freeCameraPos.y - viewHeight / 2;
    } else {
      // FOLLOW MODE: Camera volgt geselecteerde entity (Spark of Koning)
      let followEntity = spark; // Default: follow Spark
      
      if (followTarget !== 'spark') {
        // Find koning bot by blueprint_id
        const kingBot = gameState.worker_bots?.find(bot => bot.blueprint_id === followTarget);
        if (kingBot) {
          followEntity = kingBot;
        } else {
          console.log(`⚠️ King bot "${followTarget}" not found. Following Spark.`);
        }
      }
      
      // Camera gecentreerd op gevolgde entity
      cameraX = followEntity.x - viewWidth / 2;
      cameraY = followEntity.y - viewHeight / 2;
    }
    
    // Clamp camera to world bounds
    cameraX = Math.max(0, Math.min(gridSize - viewWidth, cameraX));
    cameraY = Math.max(0, Math.min(gridSize - viewHeight, cameraY));

    // Get explored tiles - FOG OF WAR DISABLED (show everything)
    let exploredTiles = [];
    for (let x = 0; x < gameState.grid_size; x++) {
      for (let y = 0; y < gameState.grid_size; y++) {
        exploredTiles.push([x, y]);
      }
    }
    // NOTE: Fog of War temporarily disabled - shows entire map
    
    const exploredSet = new Set(
      exploredTiles.map(([x, y]) => `${x},${y}`)
    );

    // Clear to black (fog of war background)
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    // Draw tiles in camera view
    for (let dy = 0; dy < viewHeight; dy++) {
      for (let dx = 0; dx < viewWidth; dx++) {
        const worldX = Math.floor(cameraX + dx);
        const worldY = Math.floor(cameraY + dy);
        
        if (worldX >= 0 && worldX < gridSize && worldY >= 0 && worldY < gridSize) {
          const isExplored = exploredSet.has(`${worldX},${worldY}`);
          
          if (isExplored) {
            // Check for water
            const isWater = gameState.water_tiles.some(w => w.x === worldX && w.y === worldY);
            if (isWater) {
              // Check if there's a bridge here
              const bridge = gameState.placed_items.find(i => i.x === worldX && i.y === worldY && (i.type === 'wooden_bridge' || i.type === 'stone_bridge'));
              
              if (bridge) {
                // Show bridge (brown/tan color)
                ctx.fillStyle = '#8B4513';  // Brown for bridge
                ctx.fillRect(dx * CELL_SIZE, dy * CELL_SIZE, CELL_SIZE, CELL_SIZE);
                // Bridge icon small
                ctx.font = `${Math.floor(CELL_SIZE * 0.4)}px Arial`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('🌉', dx * CELL_SIZE + CELL_SIZE/2, dy * CELL_SIZE + CELL_SIZE/2);
              } else {
                // Normal water (no bridge)
                ctx.fillStyle = '#1E88E5';
                ctx.fillRect(dx * CELL_SIZE, dy * CELL_SIZE, CELL_SIZE, CELL_SIZE);
              }
              continue;
            }

            // Check for mountains
            const isMountain = gameState.mountains.some(m => m.x === worldX && m.y === worldY);
            if (isMountain) {
              ctx.fillStyle = '#757575';
              ctx.fillRect(dx * CELL_SIZE, dy * CELL_SIZE, CELL_SIZE, CELL_SIZE);
              continue;
            }

            // Grass
            ctx.fillStyle = '#4CAF50';
            ctx.fillRect(dx * CELL_SIZE, dy * CELL_SIZE, CELL_SIZE, CELL_SIZE);

            // Trees (donkergroen - duidelijk zichtbaar)
            const tree = gameState.trees.find(t => t.x === worldX && t.y === worldY);
            if (tree) {
              ctx.fillStyle = tree.growth_stage === 'mature' ? '#1B5E20' : '#2E7D32';  // Veel donkerder groen
              ctx.beginPath();
              ctx.arc(dx * CELL_SIZE + CELL_SIZE/2, dy * CELL_SIZE + CELL_SIZE/2, CELL_SIZE/2 - 6, 0, Math.PI * 2);
              ctx.fill();
            }

            // Tree stumps (blijft na kappen) - NIEUW
            const stump = gameState.stumps?.find(s => s.x === worldX && s.y === worldY);
            if (stump) {
              ctx.fillStyle = '#6D4C41';  // Bruine kleur voor stronk
              ctx.beginPath();
              ctx.arc(dx * CELL_SIZE + CELL_SIZE/2, dy * CELL_SIZE + CELL_SIZE/2, CELL_SIZE/2 - 8, 0, Math.PI * 2);
              ctx.fill();
            }

            // Stones
            const stone = gameState.stones.find(s => s.x === worldX && s.y === worldY);
            if (stone) {
              ctx.fillStyle = '#9E9E9E';
              ctx.fillRect(dx * CELL_SIZE + 4, dy * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8);
            }

            // Placed items (buildings) - VISUEEL ONDERSCHEIDEN
            const item = gameState.placed_items.find(i => i.x === worldX && i.y === worldY);
            if (item) {
              // Speciale rendering voor Planter en Houthakker
              if (item.type === 'planter') {
                // Groen vierkant met bruine streep midden
                ctx.fillStyle = '#4CAF50';
                ctx.fillRect(dx * CELL_SIZE + 2, dy * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4);
                ctx.fillStyle = '#6D4C41';
                ctx.fillRect(dx * CELL_SIZE + 4, dy * CELL_SIZE + CELL_SIZE/2 - 1, CELL_SIZE - 8, 3);
              } else if (item.type === 'lumberjack') {
                // Bruin vierkant met groen randje + groene streep (OMGEDRAAID)
                ctx.fillStyle = '#4CAF50';  // Groen randje
                ctx.fillRect(dx * CELL_SIZE + 2, dy * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4);
                ctx.fillStyle = '#6D4C41';  // Bruin midden
                ctx.fillRect(dx * CELL_SIZE + 5, dy * CELL_SIZE + 5, CELL_SIZE - 10, CELL_SIZE - 10);
                ctx.fillStyle = '#4CAF50';  // Groene streep
                ctx.fillRect(dx * CELL_SIZE + 7, dy * CELL_SIZE + CELL_SIZE/2 - 1, CELL_SIZE - 14, 3);
              } else {
                // Standaard gebouw rendering
                ctx.fillStyle = '#FFC107';
                ctx.fillRect(dx * CELL_SIZE + 2, dy * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4);
              }
              
              // Icon (alleen voor niet-custom gebouwen)
              if (item.type !== 'planter' && item.type !== 'lumberjack') {
                ctx.fillStyle = '#000';
                ctx.font = `${Math.floor(CELL_SIZE * 0.6)}px Arial`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(item.icon || '🏠', dx * CELL_SIZE + CELL_SIZE/2, dy * CELL_SIZE + CELL_SIZE/2);
              }
            }
            
            // BUILDING IN PROGRESS INDICATOR
            const actionTarget = gameState.spark.action_target;
            if (gameState.spark.current_action === 'building' && actionTarget && 
                actionTarget.x === worldX && actionTarget.y === worldY) {
              // Semi-transparent blue overlay
              ctx.fillStyle = 'rgba(33, 150, 243, 0.5)';
              ctx.fillRect(dx * CELL_SIZE, dy * CELL_SIZE, CELL_SIZE, CELL_SIZE);
              
              // Hammer icon
              ctx.font = `${Math.floor(CELL_SIZE * 0.8)}px Arial`;
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText('🔨', dx * CELL_SIZE + CELL_SIZE/2, dy * CELL_SIZE + CELL_SIZE/2);
            }
          } else {
            // Fog of war
            ctx.fillStyle = '#1a1a1a';
            ctx.fillRect(dx * CELL_SIZE, dy * CELL_SIZE, CELL_SIZE, CELL_SIZE);
          }
        }
      }
    }
    
    // Draw Worker Bots (NIEUW)
    if (gameState.worker_bots && gameState.worker_bots.length > 0) {
      gameState.worker_bots.forEach(bot => {
        const dx = bot.x - cameraX;
        const dy = bot.y - cameraY;
        
        // Only draw if bot is in viewport
        if (dx >= 0 && dx < viewWidth && dy >= 0 && dy < viewHeight) {
          const botX = dx * CELL_SIZE + CELL_SIZE/2;
          const botY = dy * CELL_SIZE + CELL_SIZE/2;
          
          // Naam BOVEN alles (op top)
          const botName = bot.name || 'Bot';
          ctx.font = 'bold 10px Arial';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          ctx.fillStyle = '#000';
          ctx.fillText(botName, botX, dy * CELL_SIZE - 14);  // 14px boven de cel
          ctx.fillStyle = '#FFF';
          ctx.fillText(botName, botX - 0.5, dy * CELL_SIZE - 14.5);  // Witte outline
          
          // Icoon BOVEN HP meter (maar onder naam)
          ctx.font = 'bold 20px Arial';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(bot.icon || '🏃', botX, dy * CELL_SIZE - 2);  // Net boven de cel
          
          // State indicator bol OVER het icoon (zelfde positie)
          const stateColors = {
            'idle': '#FFD700',        // Geel bolletje = idle/niets doen
            'move_to_resource': '#FFA500',
            'gathering': '#00FF00',
            'move_to_dropoff': '#00BFFF',
            'delivering': '#FFD700',
            'detected': '#FFEB3B',
            'approach_attack': '#FF5722',
            'combat': '#F44336',
            'chase': '#E91E63',
            'flee': '#9C27B0',
            'panic': '#673AB7'
          };
          
          // King bots krijgen gouden glow (special indicator)
          const isKing = bot.type === 'king' || bot.is_king;
          const stateColor = stateColors[bot.state] || '#FFFFFF';
          
          // Bol OVER het icoon (niet linksboven, maar OP het icoon)
          const indX = botX;  // Zelfde X als icoon
          const indY = dy * CELL_SIZE - 2;  // Zelfde Y als icoon
          
          if (isKing) {
            // King bots: gouden ring + state color center OVER icoon
            ctx.fillStyle = '#FFD700';
            ctx.beginPath();
            ctx.arc(indX, indY, 6, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.fillStyle = stateColor;
            ctx.beginPath();
            ctx.arc(indX, indY, 4, 0, Math.PI * 2);
            ctx.fill();
          } else {
            // Normal bots: single color dot OVER icoon
            ctx.fillStyle = stateColor;
            ctx.beginPath();
            ctx.arc(indX, indY, 4, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      });
    }


    // Draw entities (koning bots, etc.) - ALWAYS SHOW KINGS
    const entities = gameState.entities || [];
    entities.forEach(bot => {
      // Kings are ALWAYS visible (regardless of faction view)
      const isKing = bot.type === 'king' || bot.is_king;
      
      // FILTER: Only show entities from active faction (unless it's a king)
      const shouldShow = 
        isKing || // Kings always visible!
        activeFaction === 'spark' || // Spark sees all (for now)
        !bot.faction || // No faction = always visible
        bot.faction === activeFaction; // Same faction only
      
      if (!shouldShow) return; // Skip this entity
      
      const dx = bot.x - cameraX;
      const dy = bot.y - cameraY;
      
      // Only draw if bot is in viewport
      if (dx >= 0 && dx < viewWidth && dy >= 0 && dy < viewHeight) {
        const botX = dx * CELL_SIZE + CELL_SIZE/2;
        const botY = dy * CELL_SIZE + CELL_SIZE/2;
        
        // Naam BOVEN
        const botName = bot.name || 'Bot';
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillStyle = '#000';
        ctx.fillText(botName, botX, dy * CELL_SIZE - 14);
        ctx.fillStyle = '#FFF';
        ctx.fillText(botName, botX - 0.5, dy * CELL_SIZE - 14.5);
        
        // Icoon
        ctx.font = 'bold 20px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(bot.icon || '🤖', botX, dy * CELL_SIZE - 2);
        
        // State bol OVER icoon
        const isKing = bot.type === 'king';
        const stateColor = bot.state === 'idle' ? '#FFD700' : '#4CAF50';
        
        if (isKing) {
          // King: gouden ring
          ctx.fillStyle = '#FFD700';
          ctx.beginPath();
          ctx.arc(botX, dy * CELL_SIZE - 2, 6, 0, Math.PI * 2);
          ctx.fill();
          
          ctx.fillStyle = stateColor;
          ctx.beginPath();
          ctx.arc(botX, dy * CELL_SIZE - 2, 4, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.fillStyle = stateColor;
          ctx.beginPath();
          ctx.arc(botX, dy * CELL_SIZE - 2, 4, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    });

    // Draw Spark - CLEAN zonder HP balk
    const sparkScreenX = (spark.x - cameraX) * CELL_SIZE;
    const sparkScreenY = (spark.y - cameraY) * CELL_SIZE;
    const sparkX = sparkScreenX + CELL_SIZE/2;
    const sparkY = sparkScreenY + CELL_SIZE/2;
    
    // Naam BOVEN
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillStyle = '#000';
    ctx.fillText('⚡ Spark', sparkX, sparkScreenY - 14);
    ctx.fillStyle = '#FFD700';
    ctx.fillText('⚡ Spark', sparkX - 0.5, sparkScreenY - 14.5);
    
    // Spark ICOON (groter dan runners)
    ctx.font = 'bold 28px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('⚡', sparkX, sparkScreenY - 2);
    
    // Gouden glow bol OVER icoon (zoals koning bots)
    const sparkIndX = sparkX;
    const sparkIndY = sparkScreenY - 2;
    
    // Gouden ring
    ctx.fillStyle = '#FFD700';
    ctx.beginPath();
    ctx.arc(sparkIndX, sparkIndY, 8, 0, Math.PI * 2);
    ctx.fill();
    
    // Groene center (actief)
    ctx.fillStyle = '#4CAF50';
    ctx.beginPath();
    ctx.arc(sparkIndX, sparkIndY, 5, 0, Math.PI * 2);
    ctx.fill();

    // ACTION STATUS BADGE - Toon huidige actie
    const action = spark.current_action || 'idle';
    const actionIcons = {
      'building': '🏗️',
      'gathering': '🪵',
      'exploring': '🚶',
      'fishing': '🎣',
      'sleeping': '😴',
      'fleeing': '🏃',
      'walking_home': '🏠',
      'idle': ''
    };
    
    const actionIcon = actionIcons[action] || '';
    if (actionIcon) {
      // Badge boven Spark
      const badgeX = sparkScreenX + CELL_SIZE/2;
      const badgeY = sparkScreenY - 8;
      
      // Background badge
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.beginPath();
      ctx.arc(badgeX, badgeY, 12, 0, Math.PI * 2);
      ctx.fill();
      
      // Icon
      ctx.font = 'bold 14px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(actionIcon, badgeX, badgeY);
    }

    // Draw monuments - ZELFDE SIZE ALS HUIS maar met GLOW voor herkenning
    gameState.monuments.forEach(monument => {
      const mx = (monument.x - cameraX) * CELL_SIZE;
      const my = (monument.y - cameraY) * CELL_SIZE;
      
      if (mx >= -CELL_SIZE * 3 && mx < CANVAS_SIZE && my >= -CELL_SIZE * 3 && my < CANVAS_SIZE) {
        const size = monument.size || 1;  // 1 tile = zelfde als huis
        
        // Monument met STERKE GLOW (herkenbaar maken)
        ctx.shadowBlur = 20;  // Extra strong glow
        ctx.shadowColor = monument.color || '#FFD700';
        ctx.fillStyle = monument.color || '#FFD700';
        ctx.fillRect(mx, my, size * CELL_SIZE, size * CELL_SIZE);
        ctx.shadowBlur = 0;
        
        // DIKKE border voor extra zichtbaarheid
        ctx.strokeStyle = '#FFF';
        ctx.lineWidth = 3;  // Dikker dan normaal
        ctx.strokeRect(mx, my, size * CELL_SIZE, size * CELL_SIZE);
        
        // GROTE icon (neemt hele tile)
        ctx.fillStyle = '#000';
        ctx.font = 'bold 24px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(monument.icon || '⚡', mx + (size * CELL_SIZE)/2, my + (size * CELL_SIZE)/2);
      }
    });

    // PLACEMENT PREVIEW - Highlight grid cell where item will be placed
    if (placementPreview && placementMode) {
      const previewX = placementPreview.x;
      const previewY = placementPreview.y;
      
      // Check if in camera view
      if (previewX >= cameraX && previewX < cameraX + viewWidth &&
          previewY >= cameraY && previewY < cameraY + viewHeight) {
        
        const dx = previewX - cameraX;
        const dy = previewY - cameraY;
        
        // Draw highlight box (green with alpha)
        ctx.strokeStyle = 'rgba(0, 255, 0, 0.8)';
        ctx.lineWidth = 3;
        ctx.strokeRect(dx * CELL_SIZE, dy * CELL_SIZE, CELL_SIZE, CELL_SIZE);
        
        // Draw semi-transparent fill
        ctx.fillStyle = 'rgba(0, 255, 0, 0.2)';
        ctx.fillRect(dx * CELL_SIZE, dy * CELL_SIZE, CELL_SIZE, CELL_SIZE);
        
        // Draw item icon in center
        ctx.font = `${CELL_SIZE * 0.6}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = 'white';
        ctx.fillText(
          placementMode.icon, 
          dx * CELL_SIZE + CELL_SIZE / 2, 
          dy * CELL_SIZE + CELL_SIZE / 2
        );
      }
    }

    // MINIMAP - Rechtsboven overlay
    drawMinimap(ctx, gameState);
  };

  const drawMinimap = (ctx, state) => {
    const minimapSizeVal = minimapSize;
    const minimapX = minimapPos ? minimapPos.x : (CANVAS_SIZE - minimapSizeVal - 10);
    const minimapY = minimapPos ? minimapPos.y : 10;
    const gridSize = state.grid_size;
    const pixelPerTile = minimapSizeVal / gridSize;

    // Minimap achtergrond - ZWART (niet transparent)
    ctx.fillStyle = 'rgba(20, 20, 20, 1.0)';  // Solid black
    ctx.fillRect(minimapX, minimapY, minimapSizeVal, minimapSizeVal);
    
    // Border (dikker in edit mode)
    ctx.strokeStyle = layoutEditMode ? '#FFD700' : '#4CAF50';
    ctx.lineWidth = layoutEditMode ? 3 : 2;
    ctx.strokeRect(minimapX, minimapY, minimapSizeVal, minimapSizeVal);

    // DRAW EXPLORED AREAS - Base terrain (gras)
    const exploredSet = new Set(
      state.explored_tiles.map(([x, y]) => `${x},${y}`)
    );
    
    // Draw grass for ENTIRE map (Fog of War disabled)
    ctx.fillStyle = 'rgba(76, 175, 80, 0.3)';  // Light green for grass
    for (let x = 0; x < gridSize; x++) {
      for (let y = 0; y < gridSize; y++) {
        const gx = minimapX + (x * pixelPerTile);
        const gy = minimapY + (y * pixelPerTile);
        ctx.fillRect(gx, gy, Math.max(1, pixelPerTile), Math.max(1, pixelPerTile));
      }
    }

    // DRAW TERRAIN: Water, Bergen, Bomen (echte wereld!)
    
    // 1. Water (blauw) - SHOW ALL
    ctx.fillStyle = 'rgba(33, 150, 243, 0.8)';
    state.water_tiles?.forEach(water => {
      const wx = minimapX + (water.x * pixelPerTile);
      const wy = minimapY + (water.y * pixelPerTile);
      ctx.fillRect(wx, wy, Math.max(1, pixelPerTile), Math.max(1, pixelPerTile));
    });

    // 2. Mountains (grijs/bruin) - SHOW ALL
    ctx.fillStyle = 'rgba(120, 120, 120, 0.9)';
    state.mountains?.forEach(mtn => {
      const mx = minimapX + (mtn.x * pixelPerTile);
      const my = minimapY + (mtn.y * pixelPerTile);
      ctx.fillRect(mx, my, Math.max(2, pixelPerTile * 2), Math.max(2, pixelPerTile * 2));
    });

    // 3. Trees (donkergroen) - SHOW ALL
    ctx.fillStyle = 'rgba(27, 94, 32, 0.9)';
    state.trees?.forEach(tree => {
      const tx = minimapX + (tree.x * pixelPerTile);
      const ty = minimapY + (tree.y * pixelPerTile);
      ctx.fillRect(tx, ty, Math.max(1, pixelPerTile), Math.max(1, pixelPerTile));
    });

    // 4. Placed buildings (wit/geel - belangrijker)
    state.placed_items?.forEach(item => {
      const ix = minimapX + (item.x * pixelPerTile);
      const iy = minimapY + (item.y * pixelPerTile);
      
      // Kleur op basis van type
      if (item.type === 'house') {
        ctx.fillStyle = '#FF6B6B';  // Rood voor huis
      } else if (item.type === 'warehouse') {
        ctx.fillStyle = '#FFA726';  // Oranje voor warehouse
      } else {
        ctx.fillStyle = '#FFEB3B';  // Geel voor overige buildings
      }
      
      ctx.fillRect(ix - 1, iy - 1, 3, 3);
    });

    // Draw monuments op minimap - 1 TILE zoals huis
    state.monuments.forEach(monument => {
      const mx = minimapX + (monument.x * pixelPerTile);
      const my = minimapY + (monument.y * pixelPerTile);
      
      // Monument kleur met EXTRA STRONG border (herkenning op minimap)
      ctx.fillStyle = monument.color || '#FFD700';
      ctx.fillRect(mx, my, 3, 3);  // 3px fixed (zelfde als buildings)
      
      // Dubbele border voor extra contrast
      ctx.strokeStyle = '#FFF';
      ctx.lineWidth = 1;
      ctx.strokeRect(mx - 1, my - 1, 5, 5);  // Outer border
      ctx.strokeRect(mx, my, 3, 3);  // Inner border
    });

    // Draw Spark positie - OPVALLEND
    const spark = state.spark;
    const sparkX = minimapX + (spark.x * pixelPerTile);
    const sparkY = minimapY + (spark.y * pixelPerTile);
    
    // Spark als pulserende gouden dot
    ctx.fillStyle = '#FFD700';
    ctx.beginPath();
    ctx.arc(sparkX, sparkY, 3, 0, Math.PI * 2);
    ctx.fill();
    
    // Glow effect
    ctx.strokeStyle = '#FFF';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(sparkX, sparkY, 4, 0, Math.PI * 2);
    ctx.stroke();
    
    // Draw worker bots op minimap (NIEUW)
    if (state.worker_bots && state.worker_bots.length > 0) {
      state.worker_bots.forEach(bot => {
        const botX = minimapX + (bot.x * pixelPerTile);
        const botY = minimapY + (bot.y * pixelPerTile);
        
        // King bots krijgen gouden kleur, normale bots cyaan
        const isKing = bot.type === 'king' || bot.is_king;
        ctx.fillStyle = isKing ? '#FFD700' : '#00BFFF';
        
        const size = isKing ? 3 : 2; // King bots zijn groter
        ctx.fillRect(botX - size/2, botY - size/2, size, size);
        
        // King bots krijgen extra ring
        if (isKing) {
          ctx.strokeStyle = '#FFF';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(botX, botY, 3, 0, Math.PI * 2);
          ctx.stroke();
        }
      });
    }
    
    // Draw entities (koningen) op minimap - NIEUW!
    if (state.entities && state.entities.length > 0) {
      state.entities.forEach(entity => {
        const entX = minimapX + (entity.x * pixelPerTile);
        const entY = minimapY + (entity.y * pixelPerTile);
        
        // King entities krijgen GOUDEN KROON op minimap
        const isKing = entity.type === 'king' || entity.is_king;
        
        if (isKing) {
          // Faction kleuren voor koningen
          const factionColors = {
            'terra': '#8B4513',   // Bruin
            'aqua': '#2196F3',    // Blauw
            'ignis': '#F44336',   // Rood
            'ventus': '#9E9E9E'   // Grijs
          };
          
          ctx.fillStyle = factionColors[entity.faction] || '#FFD700';
          ctx.fillRect(entX - 2, entY - 2, 4, 4);
          
          // Gouden ring (koning indicator)
          ctx.strokeStyle = '#FFD700';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(entX, entY, 4, 0, Math.PI * 2);
          ctx.stroke();
          
          // Witte outline voor visibility
          ctx.strokeStyle = '#FFF';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(entX, entY, 5, 0, Math.PI * 2);
          ctx.stroke();
        } else {
          // Andere entities (zombies, etc.)
          ctx.fillStyle = entity.type === 'undead' ? '#8B0000' : '#FF00FF';
          ctx.fillRect(entX - 1, entY - 1, 2, 2);
        }
      });
    }

    // Minimap label
    ctx.fillStyle = '#FFF';
    ctx.font = 'bold 10px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('MAP', minimapX + minimapSizeVal/2, minimapY + minimapSizeVal + 12);
    
    // Edit mode: show resize handles
    if (layoutEditMode) {
      // Resize handle bottom-right
      ctx.fillStyle = '#FFD700';
      ctx.fillRect(minimapX + minimapSizeVal - 8, minimapY + minimapSizeVal - 8, 8, 8);
    }
  };

  if (loading) {
    return (
      <div className="game-tab">
        <div className="game-loading">
          <div className="spinner"></div>
          <p>Game wordt geladen...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="game-tab">
        <div className="game-error">
          <p>❌ {error}</p>
          <button onClick={fetchGameState}>Opnieuw proberen</button>
        </div>
      </div>
    );
  }
  
  if (!gameState) {
    return <div className="game-loading">⏳ Laden...</div>;
  }

  const { spark, game_time, stats } = gameState;

  return (
    <div className="game-tab">
      {/* Audio Toggle Button - Versleepbaar (zoals legenda-knop) */}
      <button 
        className="audio-toggle-button"
        onClick={handleAudioToggle}
        onMouseDown={handleAudioMouseDown}
        style={{
          position: 'absolute',
          left: `${audioButtonPos.x}px`,
          top: `${audioButtonPos.y}px`,
          zIndex: 1000,
          width: '56px',
          height: '56px',
          padding: '0',
          background: isAudioPlaying ? 'rgba(76, 175, 80, 0.9)' : 'rgba(0, 0, 0, 0.7)',
          border: '2px solid rgba(255, 255, 255, 0.3)',
          borderRadius: '50%',
          color: 'white',
          cursor: isAudioDragging ? 'grabbing' : 'grab',
          fontSize: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'background 0.3s ease',
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)'
        }}
        title={isAudioPlaying ? "Audio pauzeren (sleep om te verplaatsen)" : "Audio afspelen (sleep om te verplaatsen)"}
      >
        {isAudioPlaying ? '🔊' : '🔇'}
      </button>
      
      <div className="game-header">
        <h1>🎮 Spark AI Mini Survival Game</h1>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button 
            className={`layout-edit-toggle ${layoutEditMode ? 'active' : ''}`}
            onClick={() => setLayoutEditMode(!layoutEditMode)}
            title="Layout aanpassen"
          >
            🔧 {layoutEditMode ? 'Klaar' : 'Layout'}
          </button>
          <div className="game-day-indicator">
            {game_time.is_day ? '☀️' : '🌙'} Dag {game_time.day}
          </div>
        </div>
      </div>

      <div className="game-container">
        <div className="game-canvas-wrapper">
          {/* Camera Mode Indicator */}
          {cameraMode === 'free' && (
            <div style={{
              position: 'absolute',
              top: '10px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'rgba(255, 152, 0, 0.9)',
              padding: '8px 16px',
              borderRadius: '20px',
              color: 'white',
              fontSize: '14px',
              fontWeight: 'bold',
              boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
              zIndex: 100,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>🎮 FREE CAM</span>
              <span style={{ fontSize: '11px', opacity: 0.8 }}>
                WASD/Arrows = Move | SPACE = Follow Spark | Click Minimap = Jump
              </span>
            </div>
          )}
          
          {/* Faction Vision Indicator */}
          {activeFaction !== 'spark' && (
            <div style={{
              position: 'absolute',
              top: cameraMode === 'free' ? '60px' : '10px',
              right: '10px',
              background: 'rgba(0, 0, 0, 0.8)',
              padding: '8px 12px',
              borderRadius: '12px',
              color: 'white',
              fontSize: '13px',
              fontWeight: 'bold',
              boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
              zIndex: 100,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              border: '1px solid rgba(255,255,255,0.3)'
            }}>
              <span>👁️</span>
              <span style={{ textTransform: 'capitalize' }}>{activeFaction} Vision</span>
              <span style={{ fontSize: '11px', opacity: 0.7 }}>(FOG OF WAR)</span>
            </div>
          )}
          
          {/* Minimap Click Overlay - Only intercept clicks within minimap */}
          {gameState && (
            <div
              onMouseDown={(e) => {
                const minimapSizeVal = minimapSize;
                const minimapX = minimapPos ? minimapPos.x : (CANVAS_SIZE - minimapSizeVal - 10);
                const minimapY = minimapPos ? minimapPos.y : 10;
                
                // Get click position relative to canvas
                const canvas = canvasRef.current;
                const rect = canvas.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const clickY = e.clientY - rect.top;
                
                // ONLY handle if click is within minimap bounds
                if (clickX >= minimapX && clickX <= minimapX + minimapSizeVal &&
                    clickY >= minimapY && clickY <= minimapY + minimapSizeVal) {
                  
                  e.preventDefault();
                  e.stopPropagation();
                  
                  // Convert to world coordinates
                  const relX = clickX - minimapX;
                  const relY = clickY - minimapY;
                  const pixelPerTile = minimapSizeVal / gameState.grid_size;
                  const worldX = Math.floor(relX / pixelPerTile);
                  const worldY = Math.floor(relY / pixelPerTile);
                  
                  // Jump camera to clicked location
                  setCameraMode('free');
                  setFreeCameraPos({ x: worldX, y: worldY });
                  console.log(`🗺️ Minimap jump to (${worldX}, ${worldY})`);
                }
                // Otherwise, let click pass through to canvas
              }}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none', // Changed to none, only handle via onMouseDown
                zIndex: 50
              }}
            />
          )}
          
          <canvas 
            ref={canvasRef}
            id="game-canvas" 
            width={CANVAS_SIZE} 
            height={CANVAS_SIZE}
            style={{ 
              outline: 'none', 
              display: 'block',
              cursor: placementMode ? 'crosshair' : 'default'
            }}
            onClick={handleCanvasClick}
            onMouseMove={handleCanvasMouseMove}
            onMouseLeave={() => setPlacementPreview(null)}
          />
        </div>
        
        {/* Game UI - Stats & Status */}
        <div className="game-stats">
          {/* Time Display */}
          <div className="ui-section time-section">
            <h3>⏰ Tijd</h3>
            <div className="time-display">
              <div className="time-main">
                Dag {game_time.day} - {String(game_time.hour).padStart(2, '0')}:{String(game_time.minute).padStart(2, '0')}
              </div>
              <div className="time-phase">
                {game_time.is_day ? '☀️ Dag' : '🌙 Nacht'}
              </div>
            </div>
          </div>

          {/* COMBINED: Spark Status + Behoeften */}
          <div className="ui-section status-section">
            <h3>⚡ Spark - Status & Behoeften</h3>
            
            {/* Health Bar */}
            <div className="stat-bar-row">
              <span className="stat-label">❤️ Health:</span>
              <div className="bar-container-new">
                <div 
                  className="bar-fill-new health-bar-new"
                  style={{ width: `${spark.health || 100}%` }}
                />
                <span className="bar-text">{spark.health || 100}</span>
              </div>
            </div>

            {/* Energy Bar */}
            <div className="stat-bar-row">
              <span className="stat-label">⚡ Energy:</span>
              <div className="bar-container-new">
                <div 
                  className="bar-fill-new energy-bar-new"
                  style={{ width: `${spark.energy || 100}%` }}
                />
                <span className="bar-text">{Math.round(spark.energy || 100)}</span>
              </div>
            </div>

            {/* Hunger Bar */}
            <div className="stat-bar-row">
              <span className="stat-label">🍖 Eten:</span>
              <div className="bar-container-new">
                <div 
                  className="bar-fill-new hunger-bar-new"
                  style={{ width: `${spark.hunger || 100}%` }}
                />
                <span className="bar-text">{Math.round(spark.hunger || 100)}</span>
              </div>
            </div>

            {/* Thirst Bar */}
            <div className="stat-bar-row">
              <span className="stat-label">💧 Drinken:</span>
              <div className="bar-container-new">
                <div 
                  className="bar-fill-new thirst-bar-new"
                  style={{ width: `${spark.thirst || 100}%` }}
                />
                <span className="bar-text">{Math.round(spark.thirst || 100)}</span>
              </div>
            </div>

            {/* Status Badges */}
            <div className="status-badges">
              {/* ACTION STATUS - Wat doet Spark? */}
              {spark.current_action === 'building' && (
                <span className="status-badge building-badge">🏗️ Building</span>
              )}
              {spark.current_action === 'gathering' && (
                <span className="status-badge gathering-badge">🪵 Gathering</span>
              )}
              {spark.current_action === 'fishing' && (
                <span className="status-badge fishing-badge">🎣 Fishing</span>
              )}
              {spark.current_action === 'sleeping' && (
                <span className="status-badge sleeping-badge">😴 Sleeping</span>
              )}
              {spark.current_action === 'fleeing' && (
                <span className="status-badge fleeing-badge">🏃 Fleeing</span>
              )}
              {spark.current_action === 'walking_home' && (
                <span className="status-badge walking-badge">🏠 Walking Home</span>
              )}
              {spark.current_action === 'exploring' && (
                <span className="status-badge exploring-badge">🚶 Exploring</span>
              )}
              {(!spark.current_action || spark.current_action === 'idle') && (
                <span className="status-badge idle-badge">✨ Idle</span>
              )}
            </div>
          </div>

          {/* Inventory Section */}
          <div className="inventory-section">
            <h3>🎒 Inventaris</h3>
            <div className="stat-item">
              <span className="stat-label">🪵 Hout:</span>
              <span className="stat-value">{spark.inventory.wood}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">🪨 Steen:</span>
              <span className="stat-value">{spark.inventory.stone}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">🐟 Vis:</span>
              <span className="stat-value">{spark.inventory.fish}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">💧 Waterflessen:</span>
              <span className="stat-value">{spark.inventory.water_bottle}</span>
            </div>
          </div>

          <div className="game-info">
            <h3>ℹ️ Info</h3>
            <div className="stat-item">
              <span className="stat-label">📅 Dag:</span>
              <span className="stat-value">{game_time.day}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">🏃 Afstand:</span>
              <span className="stat-value">{stats.distance_traveled} stappen</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">🔄 Updates:</span>
              <span className="stat-value">{stats.updates}</span>
            </div>
          </div>

          <div className="game-help">
            <h4>🌍 Actieve Wereld</h4>
            <p style={{ fontSize: '12px', color: '#aaa' }}>
              Spark bouwt automatisch zijn wereld op. Kijk mee hoe hij groeit!
            </p>
          </div>
        </div>

        {/* FACTION PANELS - Rechts van canvas */}
        <div className="faction-panels">
          <h3 className="faction-panels-title">🏛️ Fracties</h3>
          
          {factionData && gameState && (
            <>
              <FactionPanel
                name="⚡ Spark"
                color="#FFD700"
                leader="Spark"
                buildings={factionData.overview.spark.length}
                buildingsList={factionData.overview.spark}
                workers={factionData.overview.spark.filter(b => ['lumberjack', 'miner', 'fisher', 'farmer'].includes(b.type)).length}
                monumentProgress={gameState.monuments[0]?.progress || 0}
                warehouseResources={factionData.total_storage}
                sparkInventory={factionData.spark_inventory}
                isActive={followTarget === 'spark' && cameraMode === 'follow'}
                onClick={() => {
                  setCameraMode('follow');
                  setFollowTarget('spark');
                  setActiveFaction('spark'); // Show Spark's vision
                }}
              />
              <FactionPanel
                name="🌍 Terra"
                color="#8B4513"
                leader="Koning Gaia"
                buildings={factionData.overview.terra.length}
                buildingsList={factionData.overview.terra}
                workers={0}
                monumentProgress={gameState.monuments[1]?.progress || 0}
                isActive={followTarget === 'king_gaia' && cameraMode === 'follow'}
                kingData={gameState.entities?.find(e => e.type === 'king' && e.faction === 'terra')}
                onClick={() => {
                  setCameraMode('follow');
                  setFollowTarget('king_gaia');
                  setActiveFaction('terra');
                }}
              />
              <FactionPanel
                name="💧 Aqua"
                color="#2196F3"
                leader="Koning Neptune"
                buildings={factionData.overview.aqua.length}
                buildingsList={factionData.overview.aqua}
                workers={0}
                monumentProgress={gameState.monuments[2]?.progress || 0}
                isActive={followTarget === 'king_neptune' && cameraMode === 'follow'}
                kingData={gameState.entities?.find(e => e.type === 'king' && e.faction === 'aqua')}
                onClick={() => {
                  setCameraMode('follow');
                  setFollowTarget('king_neptune');
                  setActiveFaction('aqua');
                }}
              />
              <FactionPanel
                name="🔥 Ignis"
                color="#F44336"
                leader="Koning Vulcan"
                buildings={factionData.overview.ignis.length}
                buildingsList={factionData.overview.ignis}
                workers={0}
                monumentProgress={gameState.monuments[3]?.progress || 0}
                isActive={followTarget === 'king_vulcan' && cameraMode === 'follow'}
                kingData={gameState.entities?.find(e => e.type === 'king' && e.faction === 'ignis')}
                onClick={() => {
                  setCameraMode('follow');
                  setFollowTarget('king_vulcan');
                  setActiveFaction('ignis');
                }}
              />
              <FactionPanel
                name="💨 Ventus"
                color="#9E9E9E"
                leader="Koning Zephyr"
                buildings={factionData.overview.ventus.length}
                buildingsList={factionData.overview.ventus}
                workers={0}
                monumentProgress={gameState.monuments[4]?.progress || 0}
                isActive={followTarget === 'king_zephyr' && cameraMode === 'follow'}
                kingData={gameState.entities?.find(e => e.type === 'king' && e.faction === 'ventus')}
                onClick={() => {
                  setCameraMode('follow');
                  setFollowTarget('king_zephyr');
                  setActiveFaction('ventus');
                }}
              />
            </>
          )}
        </div>

      </div>

      {/* LEGEND - Uitklapbaar help panel */}
      <div 
        className="legend-container" 
        style={{ 
          left: `${legendPos.x}px`, 
          top: `${legendPos.y}px`,
          bottom: 'auto',
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
      >
        {showLegend && (
          <div className="legend-panel">
            <div className="legend-header">
              📖 Game Legenda
            </div>
            <div className="legend-content">
              <LegendSection 
                onItemSelect={(item) => setPlacementMode(item)}
                placementMode={placementMode}
              />
            </div>
          </div>
        )}
        <button 
          className="legend-toggle"
          onClick={() => setShowLegend(!showLegend)}
          onMouseDown={handleMouseDown}
          title={showLegend ? "Sluit legenda (sleep om te verplaatsen)" : "Open legenda (sleep om te verplaatsen)"}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          {showLegend ? '✕' : '❓'}
        </button>
      </div>
    </div>
  );
}

// Faction Panel Component
function FactionPanel({ name, color, leader, buildings, buildingsList, workers, monumentProgress, warehouseResources, sparkInventory, isActive, onClick, kingData }) {
  // Group buildings by type
  const buildingCounts = buildingsList ? buildingsList.reduce((acc, building) => {
    const type = building.type || 'unknown';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {}) : {};

  // Building type emoji mapping
  const buildingIcons = {
    'warehouse': '🏭',
    'house': '🏠',
    'lumberjack': '🪓',
    'miner': '⛏️',
    'fisher': '🎣',
    'farmer': '🌾',
    'planter': '🌱',
    'sawmill': '🪚',
    'mill': '🏭',
    'put': '🚰',
    'well': '💧',
    'cropfield': '🌾'
  };

  return (
    <div 
      className="faction-panel" 
      style={{ 
        borderColor: color,
        borderWidth: isActive ? '3px' : '1px',
        boxShadow: isActive ? `0 0 12px ${color}` : 'none',
        cursor: 'pointer',
        transition: 'all 0.2s ease'
      }}
      onClick={onClick}
      title="Klik om camera te volgen"
    >
      <div className="faction-header" style={{ background: `linear-gradient(135deg, ${color}33, transparent)` }}>
        <h4 style={{ color }}>
          {name}
          {isActive && <span style={{ marginLeft: '8px', fontSize: '0.8em' }}>📹</span>}
        </h4>
      </div>
      <div className="faction-stats">
        <div className="faction-stat">
          <span className="label">👑 Leider:</span>
          <span className="value">{leader}</span>
        </div>
        <div className="faction-stat">
          <span className="label">🏗️ Totaal:</span>
          <span className="value">{buildings} gebouwen</span>
        </div>
        {Object.keys(buildingCounts).length > 0 && (
          <div className="faction-stat" style={{ 
            gridColumn: '1 / -1',
            borderTop: '1px solid rgba(255,255,255,0.1)',
            paddingTop: '8px',
            marginTop: '4px'
          }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', fontSize: '0.85em' }}>
              {Object.entries(buildingCounts)
                .sort((a, b) => b[1] - a[1]) // Sort by count descending
                .map(([type, count]) => (
                  <span 
                    key={type} 
                    style={{ 
                      background: 'rgba(255,255,255,0.1)',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      whiteSpace: 'nowrap'
                    }}
                    title={type}
                  >
                    {buildingIcons[type] || '🏗️'} {count}x
                  </span>
                ))
              }
            </div>
          </div>
        )}
        
        {/* Koning Info (alleen voor koning fracties) */}
        {kingData && (
          <div className="faction-stat" style={{ 
            gridColumn: '1 / -1',
            borderTop: '1px solid rgba(255,255,255,0.2)',
            paddingTop: '8px',
            marginTop: '4px',
            background: 'rgba(255,255,255,0.05)',
            padding: '8px',
            borderRadius: '4px'
          }}>
            <div style={{ fontSize: '0.75em', color: 'rgba(255,255,255,0.6)', marginBottom: '4px' }}>
              👑 {kingData.name}:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '0.85em' }}>
              <span>📍 ({kingData.x}, {kingData.y})</span>
              <span>💚 {kingData.health}/{kingData.max_health}</span>
              {kingData.state && (
                <span style={{ 
                  fontSize: '0.75em', 
                  color: kingData.state === 'idle' ? '#FFD700' : '#4CAF50',
                  textTransform: 'uppercase'
                }}>
                  {kingData.state === 'idle' ? '⚪ Idle' : 
                   kingData.state === 'gathering' ? '🟢 Gathering' :
                   kingData.state === 'move_to_resource' ? '🟠 Moving' : kingData.state}
                </span>
              )}
            </div>
            {kingData.inventory && (
              <div style={{ display: 'flex', gap: '8px', marginTop: '4px', fontSize: '0.8em' }}>
                {kingData.inventory.wood > 0 && <span>🪵 {kingData.inventory.wood}</span>}
                {kingData.inventory.stone > 0 && <span>🪨 {kingData.inventory.stone}</span>}
              </div>
            )}
          </div>
        )}
        
        {/* Warehouse Resources (NIEUW) */}
        {warehouseResources && (
          <div className="faction-stat" style={{ 
            gridColumn: '1 / -1',
            borderTop: '1px solid rgba(255,255,255,0.2)',
            paddingTop: '8px',
            marginTop: '4px',
            background: 'rgba(255,255,255,0.05)',
            padding: '8px',
            borderRadius: '4px'
          }}>
            <div style={{ fontSize: '0.75em', color: 'rgba(255,255,255,0.6)', marginBottom: '4px' }}>
              🏭 Warehouse:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '0.85em' }}>
              {warehouseResources.wood > 0 && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  🪵 <strong>{warehouseResources.wood}</strong>
                </span>
              )}
              {warehouseResources.stone > 0 && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  🪨 <strong>{warehouseResources.stone}</strong>
                </span>
              )}
              {warehouseResources.fish > 0 && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  🐟 <strong>{warehouseResources.fish}</strong>
                </span>
              )}
              {warehouseResources.grain > 0 && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  🌾 <strong>{warehouseResources.grain}</strong>
                </span>
              )}
              {Object.values(warehouseResources).every(v => v === 0) && (
                <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8em' }}>Leeg</span>
              )}
            </div>
          </div>
        )}
        
        {/* Spark's Rugzak (alleen voor Spark) */}
        {sparkInventory && (
          <div className="faction-stat" style={{ 
            gridColumn: '1 / -1',
            paddingTop: '4px',
            marginTop: '4px'
          }}>
            <div style={{ fontSize: '0.75em', color: 'rgba(255,255,255,0.6)', marginBottom: '4px' }}>
              🎒 Rugzak Spark:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '0.85em' }}>
              {sparkInventory.wood > 0 && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  🪵 <strong>{sparkInventory.wood}</strong>
                </span>
              )}
              {sparkInventory.stone > 0 && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  🪨 <strong>{sparkInventory.stone}</strong>
                </span>
              )}
              {sparkInventory.fish > 0 && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  🐟 <strong>{sparkInventory.fish}</strong>
                </span>
              )}
            </div>
          </div>
        )}
        
        <div className="faction-stat">
          <span className="label">👷 Workers:</span>
          <span className="value">{workers}</span>
        </div>
        <div className="faction-stat">
          <span className="label">🏛️ Monument:</span>
          <span className="value">{monumentProgress.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}

// Legend Section Component
function LegendSection({ onItemSelect, placementMode }) {
  const legendItems = [
    // Natural Resources
    { category: '🌳 Natuurlijke Resources', items: [
      { type: 'tree', icon: '🌲', name: 'Boom', color: '#1B5E20' },
      { type: 'stone', icon: '🪨', name: 'Steen', color: '#757575' },
      { type: 'mountain', icon: '⛰️', name: 'Berg', color: '#8D6E63' },
      { type: 'water', icon: '💧', name: 'Water', color: '#1976D2' },
    ]},
    
    // Defensive Structures (NIEUW)
    { category: '🛡️ Verdediging', items: [
      { type: 'wall', icon: '🧱', name: 'Muur (500 HP)', color: '#795548' },
      { type: 'gate', icon: '🚪', name: 'Poort (300 HP)', color: '#A1887F' },
    ]},
    
    // Entities (Hostile & Passive)
    { category: '🧟 Entiteiten', items: [
      { type: 'zombie_barbarian', icon: '🧟', name: 'Zombie Barbaar', color: '#8B0000' },
      { type: 'wolf', icon: '🐺', name: 'Wolf', color: '#5D4037' },
      { type: 'bear', icon: '🐻', name: 'Beer', color: '#6D4C41' },
      { type: 'deer', icon: '🦌', name: 'Hert', color: '#8B4513' },
      { type: 'rabbit', icon: '🐰', name: 'Konijn', color: '#D7CCC8' },
    ]},
    
    // Koning Bots (Faction Leaders)
    { category: '👑 Koningen', items: [
      { type: 'king_gaia', icon: '👑', name: 'Koning Gaia (Terra)', color: '#8BC34A' },
      { type: 'king_neptune', icon: '🔱', name: 'Koning Neptune (Aqua)', color: '#2196F3' },
      { type: 'king_vulcan', icon: '⚒️', name: 'Koning Vulcan (Ignis)', color: '#FF5722' },
      { type: 'king_zephyr', icon: '🌪️', name: 'Koning Zephyr (Ventus)', color: '#9E9E9E' },
    ]}
  ];

  return (
    <>
      {legendItems.map((category, idx) => (
        <div key={idx} className="legend-category">
          <div className="legend-category-title">{category.category}</div>
          
          {category.items.map((item) => (
            <div 
              key={item.type}
              className={`legend-item ${placementMode?.type === item.type ? 'active' : ''}`}
              style={{ 
                cursor: 'pointer',
                background: placementMode?.type === item.type ? 'rgba(76, 175, 80, 0.2)' : 'transparent',
                border: placementMode?.type === item.type ? '2px solid #4CAF50' : 'none',
                borderRadius: '4px',
                padding: '4px'
              }}
              onClick={() => onItemSelect(item)}
              title={`Klik om ${item.name} te plaatsen`}
            >
              <div className="legend-icon" style={{ background: item.color }}>
                <div style={{ fontSize: '20px' }}>{item.icon}</div>
              </div>
              <div className="legend-description">
                <strong>{item.name}</strong>
                <small>Klik om te plaatsen</small>
              </div>
            </div>
          ))}
        </div>
      ))}
    </>
  );
}

export default GameTab;

// app.js - Final Version with Smart Button Logic and Failsafe Startup

document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram & Basic Setup ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- DOM Element References ---
    const getEl = id => document.getElementById(id);
    const loadingScreen = getEl('loading-screen');
    const mainApp = getEl('main-app');
    const statusIndicator = getEl('status-indicator');
    const statusText = getEl('status-text');
    const gameListContainer = getEl('game-list-container');
    const newGameBtn = getEl('new-game-btn');
    const filtersContainer = document.querySelector('.filters');

    // Modal Elements
    const stakeModal = getEl('stake-modal');
    const closeStakeModalBtn = getEl('close-stake-modal-btn');
    const stakeOptionsGrid = getEl('stake-options-grid');
    const cancelStakeBtn = getEl('cancel-stake-btn');
    const nextStakeBtn = getEl('next-stake-btn');
    const confirmModal = getEl('confirm-modal');
    const closeConfirmModalBtn = getEl('close-confirm-modal-btn');
    const winConditionOptions = getEl('win-condition-options');
    const createGameBtn = getEl('create-game-btn');
    const cancelConfirmBtn = getEl('cancel-confirm-btn');
    const summaryStakeAmount = getEl('summary-stake-amount');
    const summaryPrizeAmount = getEl('summary-prize-amount');

    // --- Application State ---
    let selectedStake = null;
    let selectedWinCondition = null;
    let socket = null;
    let allGames = [];
    let isConnected = false; // NEW: State to track connection status

    // --- NEW: Central Validation Logic for the Create Button ---
    // This function checks all conditions and enables/disables the button.
    const validateCreateButtonState = () => {
        if (selectedStake !== null && selectedWinCondition !== null && isConnected) {
            createGameBtn.disabled = false;
        } else {
            createGameBtn.disabled = true;
        }
    };

    // --- UI Update Functions ---
    const updateConnectionStatus = (status, text) => {
        statusIndicator.className = status;
        statusText.textContent = text;
    };

    // --- WebSocket Logic with Enhanced Callbacks ---
    function connectWebSocket() {
        updateConnectionStatus('connecting', 'Connecting...');
        console.log("Attempting to connect...");

        const userId = tg.initDataUnsafe?.user?.id || '12345';
        const socketURL = `wss://yeab-game-zone.onrender.com/ws/${userId}`; // Replace with your URL
        
        socket = new WebSocket(socketURL);

        socket.onopen = () => {
            console.log("SUCCESS: WebSocket connection established.");
            isConnected = true; // THIS IS THE KEY FIX
            updateConnectionStatus('connected', 'Connected');
            validateCreateButtonState(); // Check if the button can be enabled now
        };

        socket.onclose = () => {
            console.warn("WebSocket connection closed.");
            isConnected = false; // THIS IS THE KEY FIX
            updateConnectionStatus('disconnected', 'Disconnected');
            validateCreateButtonState(); // Always disable the button on disconnect
        };
        
        socket.onerror = (error) => {
            console.error("CRITICAL: WebSocket connection failed.", error);
            isConnected = false;
            updateConnectionStatus('disconnected', 'Failed');
            validateCreateButtonState();
        };

        socket.onmessage = (event) => {
            // (onmessage logic remains the same)
            const data = JSON.parse(event.data);
            switch (data.event) {
                case "initial_game_list": allGames = data.games; applyCurrentFilter(); break;
                case "new_game": if (!allGames.some(g => g.id === data.game.id)) { allGames.unshift(data.game); } applyCurrentFilter(); break;
                case "remove_game": allGames = allGames.filter(g => g.id !== data.gameId); removeGameCard(data.gameId); break;
            }
        };
    }

    // --- Failsafe Startup Sequence ---
    function init() {
        console.log("Initializing application...");
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            mainApp.classList.remove('hidden');
            setTimeout(() => loadingScreen.remove(), 500);
            connectWebSocket();
        }, 1500);
        setupEventListeners();
    }

    // --- Event Listeners ---
    function setupEventListeners() {
        // ... (other event listeners)

        // Update the win condition listener to use the new validation function
        winConditionOptions.addEventListener('click', e => {
            const button = e.target.closest('.win-option-btn');
            if (!button) return;
            winConditionOptions.querySelector('.selected')?.classList.remove('selected');
            button.classList.add('selected');
            selectedWinCondition = parseInt(button.dataset.win);
            validateCreateButtonState(); // THIS IS THE KEY FIX
        });

        // Update the create game button listener
        createGameBtn.addEventListener('click', () => {
            // The button is only clickable if this is true, but we double-check
            if (!socket || !isConnected || !selectedStake || !selectedWinCondition) return;
            
            socket.send(JSON.stringify({
                event: "create_game",
                payload: { stake: selectedStake, winCondition: selectedWinCondition }
            }));
            hideModal(confirmModal);
        });

        // (The rest of your event listeners remain the same)
        filtersContainer.addEventListener('click', (event) => { /* ... */ });
        newGameBtn.addEventListener('click', () => showModal(stakeModal));
        closeStakeModalBtn.addEventListener('click', () => hideModal(stakeModal));
        cancelStakeBtn.addEventListener('click', () => hideModal(stakeModal));
        nextStakeBtn.addEventListener('click', () => {
            hideModal(stakeModal);
            updateSummary();
            showModal(confirmModal);
        });
        closeConfirmModalBtn.addEventListener('click', () => hideModal(confirmModal));
        cancelConfirmBtn.addEventListener('click', () => hideModal(confirmModal));
        stakeOptionsGrid.addEventListener('click', e => {
            const button = e.target.closest('.option-btn');
            if (!button) return;
            stakeOptionsGrid.querySelector('.selected')?.classList.remove('selected');
            button.classList.add('selected');
            selectedStake = parseInt(button.dataset.stake);
            nextStakeBtn.disabled = false;
        });
    }

    // (All other helper functions like renderGameList, addGameCard, modals, etc., remain the same)
    function renderGameList(games){gameListContainer.innerHTML='';if(games.length===0){gameListContainer.innerHTML=`<h3 class="empty-state-title">No Open Games</h3>`;}else{games.forEach(addGameCard);}}
    const getWinConditionText=(c)=>({1:"1 ጠጠር ባነገሰ",2:"2 ጠጠር ባነገሰ",4:"4 ጠጠር ባነገሰ"}[c]||`${c} Piece`);
    function addGameCard(game){const card=document.createElement('div');card.className='game-card';card.id=`game-${game.id}`;card.innerHTML=`<div class="gc-player-info"><div class="gc-avatar">🧙</div><div class="gc-name-stake"><span class="gc-name">${game.creatorName||'Anonymous'}</span><span class="gc-stake">${game.stake.toFixed(2)} ETB</span></div></div><div class="gc-win-condition"><span class="gc-icon">💸</span><span class="gc-text">${getWinConditionText(game.win_condition)}</span></div><div class="gc-actions"><span class="gc-prize-label">Prize</span><span class="gc-prize">${game.prize.toFixed(2)} ETB</span><button class="gc-join-btn" data-game-id="${game.id}">Join</button></div>`;gameListContainer.appendChild(card);}
    function removeGameCard(id){const c=document.getElementById(`game-${id}`);if(c){c.remove();}if(gameListContainer.children.length===0){gameListContainer.innerHTML=`<h3 class="empty-state-title">No Open Games</h3>`;}}
    function applyCurrentFilter(){const btn=filtersContainer.querySelector('.active');if(!btn)return;const f=btn.dataset.filter;let filtered;if(f==='all'){filtered=allGames;}else if(f.includes('-')){const[min,max]=f.split('-').map(Number);filtered=allGames.filter(g=>g.stake>=min&&g.stake<=max);}else{const min=Number(f);filtered=allGames.filter(g=>g.stake>=min);}renderGameList(filtered);}
    const showModal=(m)=>{m.classList.remove('hidden');setTimeout(()=>{mainApp.style.filter='blur(5px)';m.classList.add('active');},10);};
    const hideModal=(m)=>{mainApp.style.filter='none';m.classList.remove('active');setTimeout(()=>m.classList.add('hidden'),300);};
    function updateSummary(){if(!selectedStake)return;const p=(selectedStake*2)*0.9;summaryStakeAmount.textContent=`Stake: ${selectedStake} ETB`;summaryPrizeAmount.textContent=`${p.toFixed(2)} ETB`;}

    // --- Start the Application ---
    init();
});
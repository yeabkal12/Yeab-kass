// app.js - The Final, Corrected Version with Robust Logic

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
    let socket = null;
    let allGames = [];
    let isConnected = false;

    // --- Central Validation Logic for Create Button ---
    const validateCreateButtonState = () => {
        const selectedStake = stakeOptionsGrid.querySelector('.selected');
        const selectedWinCondition = winConditionOptions.querySelector('.selected');
        
        // Enable the button only if a stake is chosen, a win condition is chosen, AND we are connected
        if (selectedStake && selectedWinCondition && isConnected) {
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

    // --- WebSocket Logic ---
    function connectWebSocket() {
        updateConnectionStatus('connecting', 'Connecting...');
        const userId = tg.initDataUnsafe?.user?.id || '12345';
        const socketURL = `wss://yeab-game-zone.onrender.com/ws/${userId}`; // IMPORTANT: USE YOUR REAL URL
        
        socket = new WebSocket(socketURL);

        socket.onopen = () => {
            isConnected = true;
            updateConnectionStatus('connected', 'Connected');
            validateCreateButtonState(); // Re-check button state on connect
        };
        socket.onclose = () => {
            isConnected = false;
            updateConnectionStatus('disconnected', 'Disconnected');
            validateCreateButtonState(); // Disable button on disconnect
        };
        socket.onerror = () => {
            isConnected = false;
            updateConnectionStatus('disconnected', 'Failed');
            validateCreateButtonState();
        };
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.event) {
                case "initial_game_list": allGames = data.games; applyCurrentFilter(); break;
                case "new_game": if (!allGames.some(g => g.id === data.game.id)) { allGames.unshift(data.game); } applyCurrentFilter(); break;
                case "remove_game": allGames = allGames.filter(g => g.id !== data.gameId); removeGameCard(data.gameId); break;
            }
        };
    }
    
    // --- UI Rendering ---
    const getWinConditionText = c => ({1:"1 ጠጠር ባነገሰ",2:"2 ጠጠር ባነገሰ",4:"4 ጠጠር ባነገሰ"}[c]||`${c} Piece`);
    function addGameCard(game){const card=document.createElement('div');card.className='game-card';card.id=`game-${game.id}`;card.innerHTML=`<div class="gc-player-info"><div class="gc-avatar">🧙</div><div class="gc-name-stake"><span class="gc-name">${game.creatorName||'Anonymous'}</span><span class="gc-stake">${game.stake.toFixed(2)} ETB</span></div></div><div class="gc-win-condition"><span class="gc-icon">💸</span><span class="gc-text">${getWinConditionText(game.win_condition)}</span></div><div class="gc-actions"><span class="gc-prize-label">Prize</span><span class="gc-prize">${game.prize.toFixed(2)} ETB</span><button class="gc-join-btn" data-game-id="${game.id}">Join</button></div>`;gameListContainer.appendChild(card);}
    function removeGameCard(id){const c=document.getElementById(`game-${id}`);if(c)c.remove();if(gameListContainer.children.length===0)gameListContainer.innerHTML=`<h3 class="empty-state-title">No Open Games</h3>`;}
    
    // --- Filter Logic ---
    function applyCurrentFilter(){const btn=filtersContainer.querySelector('.active');if(!btn)return;const f=btn.dataset.filter;let filtered;if(f==='all')filtered=allGames;else if(f.includes('-')){const[min,max]=f.split('-').map(Number);filtered=allGames.filter(g=>g.stake>=min&&g.stake<=max);}else{const min=Number(f);filtered=allGames.filter(g=>g.stake>=min);}renderGameList(filtered);}
    
    // --- Event Listeners ---
    function setupEventListeners() {
        filtersContainer.addEventListener('click', e => {const b=e.target.closest('.filter-button');if(!b)return;filtersContainer.querySelector('.active')?.classList.remove('active');b.classList.add('active');applyCurrentFilter();});
        newGameBtn.addEventListener('click', () => showModal(stakeModal));
        closeStakeModalBtn.addEventListener('click', () => hideModal(stakeModal));
        cancelStakeBtn.addEventListener('click', () => hideModal(stakeModal));
        nextStakeBtn.addEventListener('click', () => {hideModal(stakeModal);updateSummary();showModal(confirmModal);});
        closeConfirmModalBtn.addEventListener('click', () => hideModal(confirmModal));
        cancelConfirmBtn.addEventListener('click', () => hideModal(confirmModal));

        // THIS IS THE KEY FIX FOR THE STAKE SELECTION
        stakeOptionsGrid.addEventListener('click', e => {
            const button = e.target.closest('.option-btn');
            if (!button) return;
            stakeOptionsGrid.querySelector('.selected')?.classList.remove('selected');
            button.classList.add('selected');
            nextStakeBtn.disabled = false;
            // We don't call validateCreateButtonState here, that's for the next screen
        });

        // THIS IS THE KEY FIX FOR THE WIN CONDITION
        winConditionOptions.addEventListener('click', e => {
            const button = e.target.closest('.win-option-btn');
            if (!button) return;
            winConditionOptions.querySelector('.selected')?.classList.remove('selected');
            button.classList.add('selected');
            validateCreateButtonState(); // Call validation AFTER selection
        });

        createGameBtn.addEventListener('click', () => {
            if (createGameBtn.disabled) return;
            const selectedStakeEl = stakeOptionsGrid.querySelector('.selected');
            const selectedWinEl = winConditionOptions.querySelector('.selected');
            if (!socket || !selectedStakeEl || !selectedWinEl) return;
            
            socket.send(JSON.stringify({
                event: "create_game",
                payload: {
                    stake: parseInt(selectedStakeEl.dataset.stake),
                    winCondition: parseInt(selectedWinEl.dataset.win)
                }
            }));
            hideModal(confirmModal);
        });
    }

    const showModal = m => {m.classList.remove('hidden');setTimeout(() => {mainApp.style.filter='blur(5px)';m.classList.add('active');},10);};
    const hideModal = m => {mainApp.style.filter='none';m.classList.remove('active');setTimeout(() => m.classList.add('hidden'),300);};
    
    // THIS IS THE KEY FIX FOR THE SUMMARY
    function updateSummary() {
        const selectedStakeEl = stakeOptionsGrid.querySelector('.selected');
        if (!selectedStakeEl) return;
        const stake = parseInt(selectedStakeEl.dataset.stake);
        const prize = (stake * 2) * 0.9;
        summaryStakeAmount.textContent = `Stake: ${stake} ETB`;
        summaryPrizeAmount.textContent = `${prize.toFixed(2)} ETB`;
    }

    // --- Failsafe Startup Sequence ---
    function init() {
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            mainApp.classList.remove('hidden');
            setTimeout(() => loadingScreen.remove(), 500);
            connectWebSocket();
        }, 1500);
        setupEventListeners();
    }
    
    init();
});